import 'dart:convert';

import 'package:audioplayers/audioplayers.dart' as ap;
import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

/// Thin abstraction over audio playback so [TtsService] can be unit-tested
/// without touching a real audio backend.
abstract class TtsPlayer {
  Future<void> playBytes(Uint8List bytes);
  Future<void> stop();
  Future<void> dispose();
}

class AudioPlayersTtsPlayer implements TtsPlayer {
  AudioPlayersTtsPlayer() : _player = ap.AudioPlayer();

  final ap.AudioPlayer _player;

  @override
  Future<void> playBytes(Uint8List bytes) async {
    await _player.setReleaseMode(ap.ReleaseMode.stop);
    await _player.play(ap.BytesSource(bytes, mimeType: 'audio/mpeg'));
  }

  @override
  Future<void> stop() => _player.stop();

  @override
  Future<void> dispose() => _player.dispose();
}

/// Native/device TTS fallback used when the Google Edge Function is not
/// configured, unreachable, or returns unusable audio.
abstract class SystemTts {
  Future<void> speak(String text, {required String languageCode});
  Future<void> stop();
  Future<void> dispose();
}

class FlutterSystemTts implements SystemTts {
  FlutterSystemTts({FlutterTts? engine}) : _engine = engine ?? FlutterTts();

  final FlutterTts _engine;
  bool _configured = false;

  Future<void> _configure() async {
    if (_configured) return;
    await _engine.awaitSpeakCompletion(false);
    await _engine.setSpeechRate(0.42);
    await _engine.setPitch(0.9);
    await _engine.setVolume(1.0);
    if (!kIsWeb) {
      await _engine.setIosAudioCategory(
        IosTextToSpeechAudioCategory.playback,
        const [],
        IosTextToSpeechAudioMode.spokenAudio,
      );
    }
    _configured = true;
  }

  @override
  Future<void> speak(String text, {required String languageCode}) async {
    await _configure();
    await _engine.stop();
    await _engine.setLanguage(languageCode);
    await _engine.speak(text, focus: true);
  }

  @override
  Future<void> stop() => _engine.stop();

  @override
  Future<void> dispose() => _engine.stop();
}

/// Invokes the `google-tts` Edge Function and returns its decoded JSON body.
/// Injectable so tests never hit the network or need a signed-in Supabase
/// session.
typedef TtsInvoker = Future<Map<String, dynamic>> Function({
  required String text,
  required String languageCode,
});

Future<Map<String, dynamic>> _defaultInvoker({
  required String text,
  required String languageCode,
}) async {
  final response = await Supabase.instance.client.functions.invoke(
    'google-tts',
    body: {'text': text, 'languageCode': languageCode},
  );
  final data = response.data;
  if (response.status < 200 || response.status >= 300) {
    final message = data is Map && data['error'] is String
        ? data['error'] as String
        : 'google-tts failed with HTTP ${response.status}';
    throw TtsException(message);
  }
  if (data is Map) {
    final mapped = Map<String, dynamic>.from(data);
    if (mapped['error'] is String) {
      throw TtsException(mapped['error'] as String);
    }
    return mapped;
  }
  throw TtsException('google-tts returned an unexpected response shape');
}

class TtsException implements Exception {
  TtsException(this.message);

  final String message;

  @override
  String toString() => 'TtsException: $message';
}

/// Reads AI chat replies aloud via Google Cloud TTS (through the `google-tts`
/// Supabase Edge Function). Only ever called with AI text — never the
/// user's own messages.
///
/// Each [speak] call is tagged with an incrementing generation token so a
/// slow in-flight synthesis can't clobber playback started by a later call:
/// e.g. two AI replies landing close together, or the user toggling voice
/// off (or leaving chat) while a synthesis request is still in flight.
class TtsService {
  TtsService({TtsInvoker? invoker, TtsPlayer? player, SystemTts? systemTts})
      : _invoker = invoker ?? _defaultInvoker,
        _player = player ?? AudioPlayersTtsPlayer(),
        _systemTts = systemTts ?? FlutterSystemTts();

  static const Map<String, String> _languageCodes = {
    'id': 'id-ID',
    'en': 'en-US'
  };

  final TtsInvoker _invoker;
  final TtsPlayer _player;
  final SystemTts _systemTts;
  int _generation = 0;

  /// Maps the app's own language codes ('en'/'id') to the BCP-47 codes the
  /// `google-tts` function expects, defaulting to English for anything else.
  static String languageCodeFor(String appLanguage) =>
      _languageCodes[appLanguage] ?? _languageCodes['en']!;

  Future<void> speak(String text, {required String appLanguage}) async {
    final generation = ++_generation;
    await _player.stop();
    await _systemTts.stop();
    if (text.trim().isEmpty) return;

    final Map<String, dynamic> data;
    try {
      data = await _invoker(
          text: text, languageCode: languageCodeFor(appLanguage));
    } catch (_) {
      await _speakWithSystemFallback(
        text,
        languageCode: languageCodeFor(appLanguage),
        generation: generation,
      );
      return;
    }
    if (generation != _generation) return;

    final audioContentRaw = data['audioContent'];
    if (audioContentRaw is! String || audioContentRaw.isEmpty) {
      await _speakWithSystemFallback(
        text,
        languageCode: languageCodeFor(appLanguage),
        generation: generation,
      );
      return;
    }

    final Uint8List bytes;
    try {
      bytes = base64Decode(audioContentRaw);
    } catch (_) {
      await _speakWithSystemFallback(
        text,
        languageCode: languageCodeFor(appLanguage),
        generation: generation,
      );
      return;
    }
    if (generation != _generation) return;

    try {
      await _player.playBytes(bytes);
    } catch (_) {
      await _speakWithSystemFallback(
        text,
        languageCode: languageCodeFor(appLanguage),
        generation: generation,
      );
    }
  }

  Future<void> _speakWithSystemFallback(
    String text, {
    required String languageCode,
    required int generation,
  }) async {
    if (generation != _generation) return;
    try {
      await _systemTts.speak(text, languageCode: languageCode);
    } catch (_) {
      // Best-effort: TTS must never break the chat turn itself.
    }
  }

  /// Stops playback immediately and invalidates any in-flight [speak] call
  /// so it won't start playing after the fact.
  Future<void> stop() async {
    _generation++;
    await _player.stop();
    await _systemTts.stop();
  }

  Future<void> dispose() async {
    _generation++;
    await _player.dispose();
    await _systemTts.dispose();
  }
}
