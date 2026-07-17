import 'package:speech_to_text/speech_to_text.dart' as stt;

/// Thin abstraction over the platform speech recognizer so [SttService] can
/// be unit-tested without a real microphone or recognition engine.
abstract class SpeechRecognizer {
  Future<bool> initialize({
    required void Function(String status) onStatus,
    required void Function(String errorMsg, bool permanent) onError,
  });

  Future<void> listen({
    required String localeId,
    required void Function(String text, bool isFinal) onResult,
  });

  Future<void> stop();
  Future<void> cancel();
}

class PlatformSpeechRecognizer implements SpeechRecognizer {
  PlatformSpeechRecognizer() : _speech = stt.SpeechToText();

  final stt.SpeechToText _speech;

  @override
  Future<bool> initialize({
    required void Function(String status) onStatus,
    required void Function(String errorMsg, bool permanent) onError,
  }) {
    // This is what actually triggers the OS/browser mic + speech permission
    // prompt — the app's own MicPermissionModal is just an explainer shown
    // before this fires.
    return _speech.initialize(
      onStatus: onStatus,
      onError: (error) => onError(error.errorMsg, error.permanent),
    );
  }

  @override
  Future<void> listen({
    required String localeId,
    required void Function(String text, bool isFinal) onResult,
  }) {
    return _speech.listen(
      onResult: (result) => onResult(result.recognizedWords, result.finalResult),
      listenOptions: stt.SpeechListenOptions(
        localeId: localeId,
        partialResults: true,
        cancelOnError: true,
      ),
    );
  }

  @override
  Future<void> stop() => _speech.stop();

  @override
  Future<void> cancel() => _speech.cancel();
}

/// Turns spoken audio into text for the chat mic button, via the platform
/// speech recognizer (on-device on mobile/desktop, the browser's Web Speech
/// API on web). Injectable so tests never need a real microphone.
class SttService {
  SttService({SpeechRecognizer? recognizer}) : _recognizer = recognizer ?? PlatformSpeechRecognizer();

  static const Map<String, String> _localeIds = {'id': 'id_ID', 'en': 'en_US'};

  final SpeechRecognizer _recognizer;
  bool _initialized = false;
  void Function()? _onDone;

  /// Maps the app's own language codes ('en'/'id') to the locale IDs the
  /// speech recognizer expects, defaulting to English for anything else.
  static String localeIdFor(String appLanguage) => _localeIds[appLanguage] ?? _localeIds['en']!;

  /// Triggers the platform's real microphone/speech permission prompt.
  /// Returns whether recognition is available to use.
  Future<bool> requestPermission() async {
    _initialized = await _recognizer.initialize(
      onStatus: (status) {
        if (status == stt.SpeechToText.doneStatus || status == stt.SpeechToText.notListeningStatus) {
          _onDone?.call();
        }
      },
      onError: (_, __) => _onDone?.call(),
    );
    return _initialized;
  }

  /// Starts listening. [onPartialResult] fires as words are recognized;
  /// [onFinalResult] fires once with the finished transcript when recording
  /// stops naturally (silence timeout). [onDone] is a fallback that always
  /// fires when the recognizer stops for any reason (manual stop, error,
  /// natural end) so callers can reliably reset their "recording" UI state.
  Future<bool> startListening({
    required String appLanguage,
    required void Function(String text) onPartialResult,
    required void Function(String text) onFinalResult,
    required void Function() onDone,
  }) async {
    if (!_initialized && !await requestPermission()) return false;
    _onDone = onDone;
    await _recognizer.listen(
      localeId: localeIdFor(appLanguage),
      onResult: (text, isFinal) => isFinal ? onFinalResult(text) : onPartialResult(text),
    );
    return true;
  }

  /// Stops listening and delivers whatever was recognized so far as the
  /// final result — used when the user taps the mic again to end early.
  Future<void> stop() => _recognizer.stop();

  /// Stops listening and discards whatever was recognized so far.
  Future<void> cancel() {
    _onDone = null;
    return _recognizer.cancel();
  }
}
