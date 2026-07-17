import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';

import 'package:drowzydiary/services/tts_service.dart';

class _FakePlayer implements TtsPlayer {
  int playCount = 0;
  int stopCount = 0;
  int disposeCount = 0;
  Uint8List? lastBytes;

  @override
  Future<void> playBytes(Uint8List bytes) async {
    playCount++;
    lastBytes = bytes;
  }

  @override
  Future<void> stop() async {
    stopCount++;
  }

  @override
  Future<void> dispose() async {
    disposeCount++;
  }
}

void main() {
  group('TtsService.languageCodeFor', () {
    test('maps app language codes to BCP-47 codes', () {
      expect(TtsService.languageCodeFor('id'), 'id-ID');
      expect(TtsService.languageCodeFor('en'), 'en-US');
    });

    test('falls back to English for an unknown language', () {
      expect(TtsService.languageCodeFor('fr'), 'en-US');
    });
  });

  group('TtsService.speak', () {
    test('invokes with the mapped language code and plays the decoded audio', () async {
      final player = _FakePlayer();
      String? capturedText;
      String? capturedLanguageCode;
      final audioBytes = Uint8List.fromList([1, 2, 3, 4]);

      final service = TtsService(
        player: player,
        invoker: ({required String text, required String languageCode}) async {
          capturedText = text;
          capturedLanguageCode = languageCode;
          return {'audioContent': base64Encode(audioBytes)};
        },
      );

      await service.speak('Selamat malam', appLanguage: 'id');

      expect(capturedText, 'Selamat malam');
      expect(capturedLanguageCode, 'id-ID');
      expect(player.playCount, 1);
      expect(player.lastBytes, audioBytes);
    });

    test('stops any current playback before starting a new one', () async {
      final player = _FakePlayer();
      final service = TtsService(
        player: player,
        invoker: ({required String text, required String languageCode}) async {
          return {'audioContent': base64Encode(Uint8List.fromList([9]))};
        },
      );

      await service.speak('first reply', appLanguage: 'en');
      await service.speak('second reply', appLanguage: 'en');

      expect(player.stopCount, 2);
      expect(player.playCount, 2);
    });

    test('never plays audio for empty text', () async {
      final player = _FakePlayer();
      var invoked = false;
      final service = TtsService(
        player: player,
        invoker: ({required String text, required String languageCode}) async {
          invoked = true;
          return {'audioContent': ''};
        },
      );

      await service.speak('   ', appLanguage: 'en');

      expect(invoked, isFalse);
      expect(player.playCount, 0);
    });

    test('does not play when the invoker throws', () async {
      final player = _FakePlayer();
      final service = TtsService(
        player: player,
        invoker: ({required String text, required String languageCode}) async {
          throw TtsException('network error');
        },
      );

      await service.speak('hello', appLanguage: 'en');

      expect(player.playCount, 0);
    });

    test('does not play when a newer speak() call has already started', () async {
      final player = _FakePlayer();
      final firstCallGate = Completer<void>();
      final service = TtsService(
        player: player,
        invoker: ({required String text, required String languageCode}) async {
          if (text == 'slow reply') {
            await firstCallGate.future;
          }
          return {'audioContent': base64Encode(Uint8List.fromList([1]))};
        },
      );

      final slowCall = service.speak('slow reply', appLanguage: 'en');
      await service.speak('fast reply', appLanguage: 'en');
      firstCallGate.complete();
      await slowCall;

      // Only the newer ("fast reply") call's audio should have played.
      expect(player.playCount, 1);
    });

    test('stop() invalidates an in-flight speak() and halts the player', () async {
      final player = _FakePlayer();
      final gate = Completer<void>();
      final service = TtsService(
        player: player,
        invoker: ({required String text, required String languageCode}) async {
          await gate.future;
          return {'audioContent': base64Encode(Uint8List.fromList([1]))};
        },
      );

      final pending = service.speak('reply', appLanguage: 'en');
      await service.stop();
      gate.complete();
      await pending;

      expect(player.playCount, 0);
      expect(player.stopCount, greaterThanOrEqualTo(1));
    });
  });

  group('TtsService.dispose', () {
    test('disposes the underlying player', () async {
      final player = _FakePlayer();
      final service = TtsService(player: player, invoker: ({required text, required languageCode}) async => {});

      await service.dispose();

      expect(player.disposeCount, 1);
    });
  });
}
