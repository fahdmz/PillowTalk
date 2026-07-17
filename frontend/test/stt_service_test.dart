import 'package:flutter_test/flutter_test.dart';

import 'package:drowzydiary/services/stt_service.dart';

class _FakeRecognizer implements SpeechRecognizer {
  bool initializeResult = true;
  int initializeCount = 0;
  int listenCount = 0;
  int stopCount = 0;
  int cancelCount = 0;
  String? lastLocaleId;

  void Function(String status)? _onStatus;
  void Function(String errorMsg, bool permanent)? _onError;
  void Function(String text, bool isFinal)? _onResult;

  @override
  Future<bool> initialize({
    required void Function(String status) onStatus,
    required void Function(String errorMsg, bool permanent) onError,
  }) async {
    initializeCount++;
    _onStatus = onStatus;
    _onError = onError;
    return initializeResult;
  }

  @override
  Future<void> listen({
    required String localeId,
    required void Function(String text, bool isFinal) onResult,
  }) async {
    listenCount++;
    lastLocaleId = localeId;
    _onResult = onResult;
  }

  @override
  Future<void> stop() async {
    stopCount++;
  }

  @override
  Future<void> cancel() async {
    cancelCount++;
  }

  void emitResult(String text, {required bool isFinal}) => _onResult?.call(text, isFinal);
  void emitStatus(String status) => _onStatus?.call(status);
  void emitError(String errorMsg) => _onError?.call(errorMsg, false);
}

void main() {
  group('SttService.localeIdFor', () {
    test('maps app language codes to speech recognizer locale ids', () {
      expect(SttService.localeIdFor('id'), 'id_ID');
      expect(SttService.localeIdFor('en'), 'en_US');
    });

    test('falls back to English for an unknown language', () {
      expect(SttService.localeIdFor('fr'), 'en_US');
    });
  });

  group('SttService.requestPermission', () {
    test('returns the recognizer initialize() result', () async {
      final recognizer = _FakeRecognizer()..initializeResult = false;
      final service = SttService(recognizer: recognizer);

      expect(await service.requestPermission(), isFalse);
    });
  });

  group('SttService.startListening', () {
    test('initializes then listens with the mapped locale id', () async {
      final recognizer = _FakeRecognizer();
      final service = SttService(recognizer: recognizer);

      final started = await service.startListening(
        appLanguage: 'id',
        onPartialResult: (_) {},
        onFinalResult: (_) {},
        onDone: () {},
      );

      expect(started, isTrue);
      expect(recognizer.initializeCount, 1);
      expect(recognizer.listenCount, 1);
      expect(recognizer.lastLocaleId, 'id_ID');
    });

    test('does not listen when permission is denied', () async {
      final recognizer = _FakeRecognizer()..initializeResult = false;
      final service = SttService(recognizer: recognizer);

      final started = await service.startListening(
        appLanguage: 'en',
        onPartialResult: (_) {},
        onFinalResult: (_) {},
        onDone: () {},
      );

      expect(started, isFalse);
      expect(recognizer.listenCount, 0);
    });

    test('routes interim results to onPartialResult and the last one to onFinalResult', () async {
      final recognizer = _FakeRecognizer();
      final service = SttService(recognizer: recognizer);
      final partials = <String>[];
      String? finalText;

      await service.startListening(
        appLanguage: 'en',
        onPartialResult: partials.add,
        onFinalResult: (text) => finalText = text,
        onDone: () {},
      );
      recognizer.emitResult('I keep', isFinal: false);
      recognizer.emitResult('I keep thinking', isFinal: false);
      recognizer.emitResult('I keep thinking about work', isFinal: true);

      expect(partials, ['I keep', 'I keep thinking']);
      expect(finalText, 'I keep thinking about work');
    });

    test('reuses an already-granted permission on a later call', () async {
      final recognizer = _FakeRecognizer();
      final service = SttService(recognizer: recognizer);

      await service.startListening(appLanguage: 'en', onPartialResult: (_) {}, onFinalResult: (_) {}, onDone: () {});
      await service.startListening(appLanguage: 'en', onPartialResult: (_) {}, onFinalResult: (_) {}, onDone: () {});

      expect(recognizer.initializeCount, 1);
      expect(recognizer.listenCount, 2);
    });
  });

  group('SttService onDone fallback', () {
    test('fires when the recognizer reports done/notListening', () async {
      final recognizer = _FakeRecognizer();
      final service = SttService(recognizer: recognizer);
      var doneCalls = 0;

      await service.startListening(
        appLanguage: 'en',
        onPartialResult: (_) {},
        onFinalResult: (_) {},
        onDone: () => doneCalls++,
      );
      recognizer.emitStatus('done');

      expect(doneCalls, 1);
    });

    test('fires when the recognizer reports an error', () async {
      final recognizer = _FakeRecognizer();
      final service = SttService(recognizer: recognizer);
      var doneCalls = 0;

      await service.startListening(
        appLanguage: 'en',
        onPartialResult: (_) {},
        onFinalResult: (_) {},
        onDone: () => doneCalls++,
      );
      recognizer.emitError('error_no_match');

      expect(doneCalls, 1);
    });

    test('does not fire after cancel()', () async {
      final recognizer = _FakeRecognizer();
      final service = SttService(recognizer: recognizer);
      var doneCalls = 0;

      await service.startListening(
        appLanguage: 'en',
        onPartialResult: (_) {},
        onFinalResult: (_) {},
        onDone: () => doneCalls++,
      );
      await service.cancel();
      recognizer.emitStatus('done');

      expect(doneCalls, 0);
      expect(recognizer.cancelCount, 1);
    });
  });

  group('SttService.stop', () {
    test('delegates to the recognizer', () async {
      final recognizer = _FakeRecognizer();
      final service = SttService(recognizer: recognizer);

      await service.stop();

      expect(recognizer.stopCount, 1);
    });
  });
}
