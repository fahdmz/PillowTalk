import 'package:flutter/material.dart';

/// A check-in mood palette: night (dark, calming purple) or morning
/// (warm, light) — mirrors the design's NIGHT/MORNING theme tokens.
class Palette {
  const Palette({
    required this.bg,
    required this.card,
    required this.cardAlt,
    required this.accent,
    required this.accentLight,
    required this.text,
    required this.sub,
    required this.divider,
    required this.userBubble,
  });

  final Color bg;
  final Color card;
  final Color cardAlt;
  final Color accent;
  final Color accentLight;
  final Color text;
  final Color sub;
  final Color divider;
  final Color userBubble;

  static const night = Palette(
    bg: Color(0xFF161320),
    card: Color(0xFF1F1B2E),
    cardAlt: Color(0xFF2A2438),
    accent: Color(0xFF392A48),
    accentLight: Color(0xFF6B5484),
    text: Color(0xFFEDE7E2),
    sub: Color(0x8CEDE7E2),
    divider: Color(0x14EDE7E2),
    userBubble: Color(0xFF2E2740),
  );

  static const morning = Palette(
    bg: Color(0xFFF7F1E9),
    card: Color(0xFFFFFFFF),
    cardAlt: Color(0xFFF0E4D6),
    accent: Color(0xFFC08A63),
    accentLight: Color(0xFFDCB693),
    text: Color(0xFF3E332B),
    sub: Color(0x803E332B),
    divider: Color(0x143E332B),
    userBubble: Color(0xFFF0E1CC),
  );

  static const crisisBubble = Color(0x52C46D66);
}
