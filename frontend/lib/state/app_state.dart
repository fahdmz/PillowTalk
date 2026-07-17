import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart' show AuthException;

import '../data/date_format.dart';
import '../data/mock_data.dart' show sttSample;
import '../data/strings.dart';
import '../models/chat_message.dart';
import '../models/language.dart';
import '../models/recap_entry.dart';
import '../models/sleep_factor.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../services/chat_service.dart';
import '../services/profile_service.dart';
import '../services/recap_service.dart';
import '../theme/palette.dart';

enum AppScreen { auth, home, chat }

enum AuthMode { login, signup }

enum HomeTab { recap, checkin, profile }

enum CheckinMode { night, morning }

enum InputMode { stt, tts }

enum RecapFilter { all, night, morning }

/// A recap entry plus the group date-label it belongs to, resolved once a
/// user opens it — mirrors the design's `selectedEntryObj`.
class OpenRecapEntry {
  OpenRecapEntry({required this.entry, required this.dateLabelKey});

  final RecapEntry entry;
  final String dateLabelKey;
}

/// Single source of truth for the whole app. Screen/UI state lives here
/// directly; anything that needs the network goes through the services
/// (auth/chat/recap/profile) injected below rather than talking to
/// Supabase or http directly — see services/api_client.dart.
class AppState extends ChangeNotifier {
  AppState({
    AuthService? authService,
    ApiClient? apiClient,
    ChatService? chatService,
    RecapService? recapService,
    ProfileService? profileService,
  })  : _authService = authService ?? AuthService.instance(),
        _chatService = chatService ??
            ChatService(apiClient ?? ApiClient(authService ?? AuthService.instance())),
        _recapService = recapService ??
            RecapService(apiClient ?? ApiClient(authService ?? AuthService.instance())),
        _profileService = profileService ??
            ProfileService(apiClient ?? ApiClient(authService ?? AuthService.instance())) {
    _bootstrap();
  }

  final AuthService _authService;
  final ChatService _chatService;
  final RecapService _recapService;
  final ProfileService _profileService;

  AppScreen screen = AppScreen.auth;
  AuthMode authMode = AuthMode.login;
  HomeTab activeTab = HomeTab.checkin;
  CheckinMode? checkinMode;

  bool isAuthLoading = false;
  String? authError;

  final List<ChatMessage> messages = [];
  String draft = '';
  InputMode inputMode = InputMode.stt;
  bool isRecording = false;
  bool aiTyping = false;
  String? _currentSessionId;
  bool checkinCompleted = false;

  bool bedtimeMode = false;

  List<RecapGroup> recapData = [];
  bool recapsLoaded = false;
  RecapFilter recapFilter = RecapFilter.all;
  DateTime? selectedMonth;
  String? selectedEntryId;

  String? expandedFactorKey;
  List<SleepFactor> sleepFactors = [];
  List<double> weeklySleepHours = List.filled(7, 0.0);
  String? avgSleepTimeDisplay;
  String? avgWakeTimeDisplay;

  int age = 29;
  bool isEditingAge = false;
  String ageDraft = '29';
  String? fullName;

  AppLanguage lang = AppLanguage.en;

  Timer? _recordingTimer;

  UiStrings get t => uiStringsFor(lang);
  Palette get palette => checkinMode == CheckinMode.morning ? Palette.morning : Palette.night;

  // --- bootstrap / auth ---------------------------------------------------

  /// Supabase sessions persist ~30 days, so on a fresh launch we may already
  /// be signed in — skip straight to Home in that case instead of showing
  /// the auth screen.
  Future<void> _bootstrap() async {
    if (_authService.isSignedIn) {
      screen = AppScreen.home;
      notifyListeners();
      await _loadHomeData();
    }
  }

  void setAuthMode(AuthMode mode) {
    authMode = mode;
    authError = null;
    notifyListeners();
  }

  Future<void> logIn({required String email, required String password}) async {
    authError = null;
    isAuthLoading = true;
    notifyListeners();
    try {
      await _authService.signIn(email: email, password: password);
      await goHome();
    } on AuthException catch (e) {
      authError = e.message;
    } catch (_) {
      authError = 'Something went wrong. Please try again.';
    } finally {
      isAuthLoading = false;
      notifyListeners();
    }
  }

  Future<void> signUp({
    required String email,
    required String password,
    required String fullName,
  }) async {
    authError = null;
    isAuthLoading = true;
    notifyListeners();
    try {
      await _authService.signUp(email: email, password: password, fullName: fullName);
      await goHome();
    } on AuthException catch (e) {
      authError = e.message;
    } catch (_) {
      authError = 'Something went wrong. Please try again.';
    } finally {
      isAuthLoading = false;
      notifyListeners();
    }
  }

  // --- navigation ---------------------------------------------------------

  Future<void> goHome() async {
    screen = AppScreen.home;
    notifyListeners();
    await _loadHomeData();
  }

  Future<void> _loadHomeData() async {
    await Future.wait([
      loadProfile(),
      loadRecaps(),
      loadWeeklySleep(),
      loadSleepFactors(),
    ]);
  }

  void setTab(HomeTab tab) {
    screen = AppScreen.home;
    activeTab = tab;
    notifyListeners();
  }

  Future<void> selectCheckin(CheckinMode mode) async {
    screen = AppScreen.chat;
    checkinMode = mode;
    checkinCompleted = false;
    messages.clear();
    _currentSessionId = null;
    notifyListeners();

    try {
      final started = await _chatService.startSession(checkinMode: mode.name, language: lang.name);
      _currentSessionId = started.sessionId;
      messages.add(started.greeting);
      notifyListeners();
    } catch (_) {
      // Leave the chat empty; the input row still lets the user retry by
      // typing, which will surface the same error again.
    }
  }

  Future<void> exitChat() async {
    final sessionId = _currentSessionId;
    screen = AppScreen.home;
    activeTab = HomeTab.checkin;
    _recordingTimer?.cancel();
    isRecording = false;
    aiTyping = false;
    notifyListeners();

    if (sessionId != null && !checkinCompleted) {
      try {
        await _chatService.endSessionEarly(sessionId);
      } catch (_) {
        // best-effort — the session just stays 'active' server-side
      }
    }
    await loadRecaps();
  }

  Future<void> logOut() async {
    try {
      await _authService.signOut();
    } catch (_) {
      // fall through to local reset regardless
    }
    screen = AppScreen.auth;
    authMode = AuthMode.login;
    activeTab = HomeTab.checkin;
    recapData = [];
    recapsLoaded = false;
    sleepFactors = [];
    weeklySleepHours = List.filled(7, 0.0);
    messages.clear();
    notifyListeners();
  }

  // --- chat -----------------------------------------------------------------

  void updateDraft(String value) {
    draft = value;
    notifyListeners();
  }

  void toggleInputMode() {
    inputMode = inputMode == InputMode.stt ? InputMode.tts : InputMode.stt;
    notifyListeners();
  }

  Future<void> sendMessage([String? overrideText]) async {
    final text = (overrideText ?? draft).trim();
    if (text.isEmpty || checkinCompleted) return;
    final sessionId = _currentSessionId;
    if (sessionId == null) return;

    messages.add(ChatMessage(id: DateTime.now().microsecondsSinceEpoch, sender: MessageSender.user, text: text));
    draft = '';
    aiTyping = true;
    notifyListeners();

    try {
      final result = await _chatService.sendMessage(sessionId: sessionId, text: text, language: lang.name);
      messages.add(result.aiMessage);
      if (result.sessionCompleted) checkinCompleted = true;
    } catch (_) {
      messages.add(ChatMessage(
        id: DateTime.now().microsecondsSinceEpoch,
        sender: MessageSender.ai,
        text: "Sorry, I'm having trouble connecting right now. Please try again.",
      ));
    } finally {
      aiTyping = false;
      notifyListeners();
    }
  }

  void startVoiceInput() {
    // STT (Whisper) isn't wired up yet — this still simulates a recognized
    // phrase so the voice-input UI can be exercised end to end.
    if (draft.trim().isNotEmpty) {
      sendMessage();
      return;
    }
    isRecording = true;
    notifyListeners();
    _recordingTimer?.cancel();
    _recordingTimer = Timer(const Duration(milliseconds: 1400), () {
      isRecording = false;
      sendMessage(sttSample);
    });
  }

  // --- recap ------------------------------------------------------------

  Future<void> loadRecaps() async {
    try {
      final items = await _recapService.listRecaps();
      final groups = <RecapGroup>[];
      DateTime? lastDay;
      for (final item in items) {
        final day = DateTime(item.date.year, item.date.month, item.date.day);
        final entry = RecapEntry(
          id: item.id,
          time: item.time,
          isNight: item.isNight,
          preview: item.preview ?? '',
        );
        if (lastDay == day && groups.isNotEmpty) {
          groups.last.items.add(entry);
        } else {
          groups.add(RecapGroup(dateLabelKey: recapDateLabelKey(day), dateValue: day, items: [entry]));
          lastDay = day;
        }
      }
      recapData = groups;
      recapsLoaded = true;
      notifyListeners();
    } catch (_) {
      // keep whatever was last loaded rather than wiping the screen
    }
  }

  void setRecapFilter(RecapFilter filter) {
    recapFilter = filter;
    notifyListeners();
  }

  void updateSelectedMonth(DateTime? month) {
    selectedMonth = month;
    notifyListeners();
  }

  void clearSelectedMonth() {
    selectedMonth = null;
    notifyListeners();
  }

  void openRecapEntry(String id) {
    selectedEntryId = id;
    notifyListeners();
    _loadRecapTranscript(id);
  }

  Future<void> _loadRecapTranscript(String id) async {
    try {
      final detail = await _recapService.getRecap(id);
      for (final group in recapData) {
        for (final item in group.items) {
          if (item.id == id) item.transcript = detail.transcript;
        }
      }
      notifyListeners();
    } catch (_) {
      // detail screen just shows an empty transcript
    }
  }

  void closeRecapDetail() {
    selectedEntryId = null;
    notifyListeners();
  }

  Future<void> deleteEntry() async {
    final id = selectedEntryId;
    if (id == null) return;
    for (final group in recapData) {
      group.items.removeWhere((it) => it.id == id);
    }
    recapData.removeWhere((group) => group.items.isEmpty);
    selectedEntryId = null;
    notifyListeners();

    try {
      await _recapService.deleteRecap(id);
    } catch (_) {
      // already removed locally; a stale row server-side will just get
      // filtered out again next time loadRecaps() runs
    }
  }

  List<RecapGroup> get filteredRecapGroups {
    return recapData
        .where((g) => selectedMonth == null ||
            (g.dateValue.year == selectedMonth!.year && g.dateValue.month == selectedMonth!.month))
        .map((g) {
          final items = g.items.where((it) {
            switch (recapFilter) {
              case RecapFilter.all:
                return true;
              case RecapFilter.night:
                return it.isNight;
              case RecapFilter.morning:
                return !it.isNight;
            }
          }).toList();
          return RecapGroup(dateLabelKey: g.dateLabelKey, dateValue: g.dateValue, items: items);
        })
        .where((g) => g.items.isNotEmpty)
        .toList();
  }

  String recapGroupLabel(RecapGroup group) {
    final base = dateLabelTranslations[lang]![group.dateLabelKey] ?? group.dateLabelKey;
    if (isWeekdayLabelKey(group.dateLabelKey)) {
      return '$base · ${formatShortDate(group.dateValue, lang)}';
    }
    return base;
  }

  String recapItemTimeDisplay(RecapGroup group, RecapEntry entry) {
    if (group.dateLabelKey == 'Last week') {
      return '${formatShortDate(group.dateValue, lang)} · ${entry.time}';
    }
    return entry.time;
  }

  String get monthFilterLabel =>
      selectedMonth != null ? formatMonthYear(selectedMonth!, lang) : t.month;

  OpenRecapEntry? get openEntry {
    if (selectedEntryId == null) return null;
    for (final group in recapData) {
      for (final item in group.items) {
        if (item.id == selectedEntryId) {
          return OpenRecapEntry(entry: item, dateLabelKey: group.dateLabelKey);
        }
      }
    }
    return null;
  }

  // --- profile ------------------------------------------------------------

  Future<void> loadProfile() async {
    try {
      final profile = await _profileService.getProfile();
      age = profile.age ?? age;
      ageDraft = '$age';
      lang = profile.language == 'id' ? AppLanguage.id : AppLanguage.en;
      bedtimeMode = profile.bedtimeMode;
      fullName = profile.fullName;
      notifyListeners();
    } catch (_) {
      // keep local defaults if the profile can't be fetched yet
    }
  }

  Future<void> loadWeeklySleep() async {
    try {
      final stats = await _profileService.getWeeklySleep();
      const order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
      final hours = List<double>.filled(7, 0.0);
      for (final point in stats.week) {
        final index = order.indexOf(point.day);
        if (index != -1) hours[index] = point.hours;
      }
      weeklySleepHours = hours;
      avgSleepTimeDisplay = stats.avgSleepTime;
      avgWakeTimeDisplay = stats.avgWakeTime;
      notifyListeners();
    } catch (_) {
      // chart just shows zeros until this succeeds
    }
  }

  Future<void> loadSleepFactors() async {
    try {
      final factors = await _profileService.getSleepFactors();
      sleepFactors = factors
          .map((f) => SleepFactor(
                nameKey: f.nameKey,
                level: f.level,
                occurrences: f.occurrences
                    .map((o) => SleepOccurrence(
                          checkinLabelKey: o.checkinLabelKey,
                          time: formatOccurrenceTime(o.time),
                        ))
                    .toList(),
              ))
          .toList();
      notifyListeners();
    } catch (_) {
      // Profile tab just shows no influencers yet
    }
  }

  void toggleFactor(String nameKey) {
    expandedFactorKey = expandedFactorKey == nameKey ? null : nameKey;
    notifyListeners();
  }

  Future<void> toggleBedtime() async {
    bedtimeMode = !bedtimeMode;
    notifyListeners();
    try {
      await _profileService.updateProfile(bedtimeMode: bedtimeMode);
    } catch (_) {
      // best-effort sync; local toggle already reflects the user's tap
    }
  }

  void startEditAge() {
    isEditingAge = true;
    ageDraft = '$age';
    notifyListeners();
  }

  void updateAgeDraft(String value) {
    ageDraft = value;
    notifyListeners();
  }

  Future<void> saveAge() async {
    final parsed = int.tryParse(ageDraft);
    if (parsed != null && parsed > 0) age = parsed;
    isEditingAge = false;
    notifyListeners();
    try {
      await _profileService.updateProfile(age: age);
    } catch (_) {
      // best-effort sync
    }
  }

  Future<void> setLang(AppLanguage value) async {
    lang = value;
    notifyListeners();
    try {
      await _profileService.updateProfile(language: value.name);
    } catch (_) {
      // best-effort sync
    }
  }

  @override
  void dispose() {
    _recordingTimer?.cancel();
    super.dispose();
  }
}
