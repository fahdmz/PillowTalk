import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart'
    show AuthChangeEvent, AuthException, AuthState;

import '../data/date_format.dart';
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
import '../services/stt_service.dart';
import '../services/tts_service.dart';
import '../theme/palette.dart';

enum AppScreen { auth, home, chat }

enum AuthMode { login, signup }

enum HomeTab { recap, checkin, profile }

enum CheckinMode { night, morning }

enum InputMode { stt, tts }

enum RecapFilter { all, night, morning }

enum MicPermStatus { unasked, granted, denied }

const _connectionErrorText =
    "Sorry, I'm having trouble connecting right now. Please try again.";

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
    TtsService? ttsService,
    SttService? sttService,
  })  : _authService = authService ?? AuthService.instance(),
        _chatService = chatService ??
            ChatService(
                apiClient ?? ApiClient(authService ?? AuthService.instance())),
        _recapService = recapService ??
            RecapService(
                apiClient ?? ApiClient(authService ?? AuthService.instance())),
        _profileService = profileService ??
            ProfileService(
                apiClient ?? ApiClient(authService ?? AuthService.instance())),
        _ttsService = ttsService ?? TtsService(),
        _sttService = sttService ?? SttService() {
    _bootstrap();
    // Google OAuth completes via an external browser + deep-link redirect,
    // not a value we can await directly — this is what actually moves us
    // to Home once that redirect lands and Supabase picks up the session.
    _authSub = _authService.onAuthStateChange.listen((data) {
      if (data.event == AuthChangeEvent.signedIn && screen == AppScreen.auth) {
        goHome();
      }
    });
  }

  final AuthService _authService;
  final ChatService _chatService;
  final RecapService _recapService;
  final ProfileService _profileService;
  final TtsService _ttsService;
  final SttService _sttService;
  StreamSubscription<AuthState>? _authSub;

  AppScreen screen = AppScreen.auth;
  AuthMode authMode = AuthMode.login;
  HomeTab activeTab = HomeTab.checkin;
  CheckinMode? checkinMode;

  bool isAuthLoading = false;
  bool isGoogleLoading = false;
  String? authError;

  final List<ChatMessage> messages = [];
  String draft = '';
  InputMode inputMode = InputMode.stt;
  bool isRecording = false;
  bool aiTyping = false;
  String? _currentSessionId;
  bool checkinCompleted = false;

  MicPermStatus micPermStatus = MicPermStatus.unasked;
  bool showMicPermModal = false;

  bool bedtimeMode = false;
  String quietHoursStart = '22:00';
  String quietHoursEnd = '07:00';

  List<RecapGroup> recapData = [];
  bool recapsLoaded = false;
  RecapFilter recapFilter = RecapFilter.all;
  DateTime? selectedMonth;
  String? selectedEntryId;
  bool showDeleteConfirm = false;

  /// Which reminder the "preview night/morning reminder" links in the
  /// Check-in tab are currently showing in [NotificationBanner].
  CheckinMode? notifPreviewType;
  bool notifOpen = false;
  Timer? _notifTimer;

  String? expandedFactorKey;
  List<SleepFactor> sleepFactors = [];
  List<double> weeklySleepHours = List.filled(7, 0.0);
  String? avgSleepTimeDisplay;
  String? avgWakeTimeDisplay;

  int age = 29;
  bool isEditingAge = false;
  String ageDraft = '29';
  String? fullName;

  AppLanguage lang = AppLanguage.id;

  UiStrings get t => uiStringsFor(lang);
  Palette get palette =>
      checkinMode == CheckinMode.morning ? Palette.morning : Palette.night;

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
      await _authService.signUp(
          email: email, password: password, fullName: fullName);
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

  /// Launches the Google OAuth flow. This returns as soon as the external
  /// browser opens — it does NOT mean the user is signed in yet. The actual
  /// navigation to Home happens in the `onAuthStateChange` listener set up
  /// in the constructor, once the OAuth redirect lands back in the app.
  Future<void> signInWithGoogle() async {
    authError = null;
    isGoogleLoading = true;
    notifyListeners();
    try {
      await _authService.signInWithGoogle();
    } on AuthException catch (e) {
      authError = e.message;
    } catch (_) {
      authError = 'Something went wrong. Please try again.';
    } finally {
      isGoogleLoading = false;
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

    final sessionId = await _ensureSession();
    if (sessionId == null) {
      messages.add(const ChatMessage(
        id: 'session-start-failed',
        sender: MessageSender.ai,
        text: _connectionErrorText,
      ));
    }
    notifyListeners();
  }

  /// Starts a chat session if one isn't already active. Used both when
  /// first entering the chat and as a retry path from [sendMessage], so a
  /// failed [selectCheckin] doesn't leave the input row permanently dead.
  ///
  /// The backend resumes today's in-progress session for this check-in type
  /// if one exists (or hands back today's already-completed one, read-only,
  /// enforcing one check-in of each type per day) — either way it returns
  /// the full message history, which replaces whatever's currently loaded.
  Future<String?> _ensureSession() async {
    if (_currentSessionId != null) return _currentSessionId;
    final mode = checkinMode;
    if (mode == null) return null;
    try {
      final started = await _chatService.startSession(
          checkinMode: mode.name, language: lang.name);
      _currentSessionId = started.sessionId;
      checkinCompleted = started.sessionStatus == 'completed';
      messages
        ..clear()
        ..addAll(started.messages);
      return started.sessionId;
    } catch (_) {
      return null;
    }
  }

  /// Leaving chat is just navigation now, not an end-of-session action — an
  /// in-progress check-in stays active server-side so reopening the same
  /// type later today resumes it instead of starting over. It only gets
  /// finalized (recap generated) once a new day rolls it over in
  /// `_ensureSession`, or `session_status` comes back completed on its own.
  Future<void> exitChat() async {
    screen = AppScreen.home;
    activeTab = HomeTab.checkin;
    await _sttService.cancel();
    isRecording = false;
    aiTyping = false;
    await _ttsService.stop();
    notifyListeners();
    await loadRecaps();
  }

  Future<void> logOut() async {
    await _ttsService.stop();
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
    if (inputMode == InputMode.tts) {
      // Turning voice replies on reads the latest AI reply immediately,
      // then every new one as it arrives (see sendMessage).
      final lastAiMessage = messages.lastWhere(
        (m) => m.sender == MessageSender.ai,
        orElse: () => const ChatMessage(id: '', sender: MessageSender.ai),
      );
      _speak(lastAiMessage);
    } else {
      unawaited(_ttsService.stop());
    }
  }

  /// Speaks an AI message aloud if voice replies are on. Never called with
  /// the user's own messages.
  void _speak(ChatMessage message) {
    if (inputMode != InputMode.tts) return;
    final text = _spokenTextFor(message);
    if (text == null) return;
    unawaited(_ttsService.speak(text, appLanguage: lang.name));
  }

  Future<void> sendMessage([String? overrideText]) async {
    if (isRecording) {
      // Manually sending (e.g. tapping the arrow that a live partial STT
      // result turned into) must stop the still-listening recognizer, or a
      // late final result would silently send a second message.
      unawaited(_sttService.cancel());
      isRecording = false;
    }
    final text = (overrideText ?? draft).trim();
    // Today's already-completed check-ins render read-only (see ChatScreen,
    // which hides the input row entirely for these) — no input reaches here.
    if (text.isEmpty || checkinCompleted) return;

    final sessionId = await _ensureSession();
    if (sessionId == null) {
      messages.add(ChatMessage(
        id: DateTime.now().microsecondsSinceEpoch,
        sender: MessageSender.ai,
        text: _connectionErrorText,
      ));
      notifyListeners();
      return;
    }

    messages.add(ChatMessage(
        id: DateTime.now().microsecondsSinceEpoch,
        sender: MessageSender.user,
        text: text));
    draft = '';
    aiTyping = true;
    notifyListeners();

    try {
      final result = await _chatService.sendMessage(
          sessionId: sessionId, text: text, language: lang.name);
      messages.add(result.aiMessage);
      _speak(result.aiMessage);
      _refreshStatsAfterChatTurn(sessionCompleted: result.sessionCompleted);
      if (result.sessionCompleted) checkinCompleted = true;
    } catch (_) {
      messages.add(ChatMessage(
        id: DateTime.now().microsecondsSinceEpoch,
        sender: MessageSender.ai,
        text: _connectionErrorText,
      ));
    } finally {
      aiTyping = false;
      notifyListeners();
    }
  }

  void _refreshStatsAfterChatTurn({required bool sessionCompleted}) {
    unawaited(Future.wait([
      loadWeeklySleep(),
      loadSleepFactors(),
      if (sessionCompleted) loadRecaps(),
    ]));
  }

  void startVoiceInput() {
    if (draft.trim().isNotEmpty) {
      sendMessage();
      return;
    }
    if (isRecording) {
      // Tapping the mic again while it's listening ends the recording early
      // and sends whatever was recognized so far.
      _sttService.stop();
      return;
    }
    if (micPermStatus == MicPermStatus.unasked) {
      showMicPermModal = true;
      notifyListeners();
      return;
    }
    if (micPermStatus == MicPermStatus.denied) return;
    _beginRecording();
  }

  void _beginRecording() {
    isRecording = true;
    notifyListeners();
    _sttService.startListening(
      appLanguage: lang.name,
      onPartialResult: (text) {
        draft = text;
        notifyListeners();
      },
      onFinalResult: (text) {
        isRecording = false;
        draft = '';
        notifyListeners();
        if (text.trim().isNotEmpty) sendMessage(text);
      },
      onDone: () {
        // Fallback for when recognition stops without ever delivering a
        // final result (e.g. a permission/engine error) so the mic button
        // doesn't get stuck showing "listening".
        if (isRecording) {
          isRecording = false;
          notifyListeners();
        }
      },
    );
  }

  Future<void> allowMicPerm() async {
    showMicPermModal = false;
    notifyListeners();
    final granted = await _sttService.requestPermission();
    micPermStatus = granted ? MicPermStatus.granted : MicPermStatus.denied;
    notifyListeners();
    if (granted) _beginRecording();
  }

  void denyMicPerm() {
    micPermStatus = MicPermStatus.denied;
    showMicPermModal = false;
    notifyListeners();
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
          date: item.date,
          time: item.time,
          isNight: item.isNight,
          preview: item.preview ?? '',
          title: item.title,
          summary: item.summary,
        );
        if (lastDay == day && groups.isNotEmpty) {
          groups.last.items.add(entry);
        } else {
          groups.add(RecapGroup(
              dateLabelKey: recapDateLabelKey(day),
              dateValue: day,
              items: [entry]));
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

  void requestDeleteEntry() {
    showDeleteConfirm = true;
    notifyListeners();
  }

  void cancelDeleteEntry() {
    showDeleteConfirm = false;
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
    showDeleteConfirm = false;
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
        .where((g) =>
            selectedMonth == null ||
            (g.dateValue.year == selectedMonth!.year &&
                g.dateValue.month == selectedMonth!.month))
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
          return RecapGroup(
              dateLabelKey: g.dateLabelKey,
              dateValue: g.dateValue,
              items: items);
        })
        .where((g) => g.items.isNotEmpty)
        .toList();
  }

  String recapGroupLabel(RecapGroup group) {
    final base =
        dateLabelTranslations[lang]![group.dateLabelKey] ?? group.dateLabelKey;
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

  // --- notification preview ------------------------------------------------

  void previewNightNotif() => _showNotifBanner(CheckinMode.night);
  void previewMorningNotif() => _showNotifBanner(CheckinMode.morning);

  void _showNotifBanner(CheckinMode type) {
    _notifTimer?.cancel();
    notifPreviewType = type;
    notifOpen = true;
    notifyListeners();
    _notifTimer = Timer(const Duration(seconds: 6), () {
      notifOpen = false;
      notifyListeners();
    });
  }

  void dismissNotifBanner() {
    _notifTimer?.cancel();
    notifOpen = false;
    notifyListeners();
  }

  /// Tapping the banner itself, like tapping a real push notification, deep
  /// links straight into that check-in's chat.
  Future<void> openNotifBanner() async {
    final type = notifPreviewType;
    _notifTimer?.cancel();
    notifOpen = false;
    notifyListeners();
    if (type != null) await selectCheckin(type);
  }

  // --- profile ------------------------------------------------------------

  Future<void> loadProfile() async {
    try {
      final profile = await _profileService.getProfile();
      age = profile.age ?? age;
      ageDraft = '$age';
      lang = profile.language == 'id' ? AppLanguage.id : AppLanguage.en;
      bedtimeMode = profile.bedtimeMode;
      quietHoursStart = profile.quietHoursStart;
      quietHoursEnd = profile.quietHoursEnd;
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

  /// "10:00 PM – 7:00 AM" style label built from the 24h "HH:MM" values the
  /// backend stores.
  String get quietHoursDisplay =>
      '${_format12Hour(quietHoursStart)} – ${_format12Hour(quietHoursEnd)}';

  Future<void> updateQuietHours(String start, String end) async {
    quietHoursStart = start;
    quietHoursEnd = end;
    notifyListeners();
    try {
      await _profileService.updateProfile(
          quietHoursStart: start, quietHoursEnd: end);
    } catch (_) {
      // best-effort sync; local value already reflects the user's pick
    }
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
    unawaited(_sttService.cancel());
    _notifTimer?.cancel();
    _authSub?.cancel();
    unawaited(_ttsService.dispose());
    super.dispose();
  }
}

/// Text to actually speak for a chat message: its own text, or — for a
/// crisis message, whose text is intentionally split into
/// prefix/phone/suffix for the tappable phone link — those parts joined
/// back together, since that guidance matters at least as much read aloud.
String? _spokenTextFor(ChatMessage message) {
  final text = message.text;
  if (text != null && text.trim().isNotEmpty) return text;
  if (!message.isCrisis) return null;
  final parts = [
    message.crisisPrefix,
    message.crisisPhone,
    message.crisisSuffix
  ].where((part) => part != null && part.trim().isNotEmpty).join(' ');
  return parts.isEmpty ? null : parts;
}

/// "22:00" -> "10:00 PM", "07:00" -> "7:00 AM".
String _format12Hour(String hhmm) {
  final parts = hhmm.split(':');
  final hour24 = int.tryParse(parts[0]) ?? 0;
  final minute = parts.length > 1 ? parts[1].padLeft(2, '0') : '00';
  final period = hour24 < 12 ? 'AM' : 'PM';
  final hour12 = hour24 % 12 == 0 ? 12 : hour24 % 12;
  return '$hour12:$minute $period';
}
