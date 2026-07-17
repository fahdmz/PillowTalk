import 'dart:convert';
import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart' as ap;
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
  Future<void> playBytes(Uint8List bytes) => _player.play(ap.BytesSource(bytes));

  @override
  Future<void> stop() => _player.stop();

  @override
  Future<void> dispose() => _player.dispose();
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
  if (data is Map) return Map<String, dynamic>.from(data);
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
  TtsService({TtsInvoker? invoker, TtsPlayer? player})
      : _invoker = invoker ?? _defaultInvoker,
        _player = player ?? AudioPlayersTtsPlayer();

  static const Map<String, String> _languageCodes = {'id': 'id-ID', 'en': 'en-US'};

  final TtsInvoker _invoker;
  final TtsPlayer _player;
  int _generation = 0;

  /// Maps the app's own language codes ('en'/'id') to the BCP-47 codes the
  /// `google-tts` function expects, defaulting to English for anything else.
  static String languageCodeFor(String appLanguage) =>
      _languageCodes[appLanguage] ?? _languageCodes['en']!;

  Future<void> speak(String text, {required String appLanguage}) async {
    final generation = ++_generation;
    await _player.stop();
    if (text.trim().isEmpty) return;

    final Map<String, dynamic> data;
    try {
      data = await _invoker(text: text, languageCode: languageCodeFor(appLanguage));
    } catch (_) {
      // Best-effort — a failed synthesis just means this reply stays
      // silent; it must never break the chat turn itself.
      return;
    }
    if (generation != _generation) return;

    final audioContentRaw = data['audioContent'];
    if (audioContentRaw is! String || audioContentRaw.isEmpty) return;

    final Uint8List bytes;
    try {
      bytes = base64Decode(audioContentRaw);
    } catch (_) {
      return;
    }
    if (generation != _generation) return;

    await _player.playBytes(bytes);
  }

  /// Stops playback immediately and invalidates any in-flight [speak] call
  /// so it won't start playing after the fact.
  Future<void> stop() async {
    _generation++;
    await _player.stop();
  }

  Future<void> dispose() async {
    _generation++;
    await _player.dispose();
  }
}
