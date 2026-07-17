import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'palette.dart';

ThemeData buildAppTheme(Palette palette) {
  final base = ThemeData(
    brightness: palette == Palette.night ? Brightness.dark : Brightness.light,
    scaffoldBackgroundColor: palette.bg,
    useMaterial3: true,
    fontFamily: GoogleFonts.nunito().fontFamily,
  );
  return base.copyWith(
    textTheme: GoogleFonts.nunitoTextTheme(base.textTheme).apply(
      bodyColor: palette.text,
      displayColor: palette.text,
    ),
    colorScheme: base.colorScheme.copyWith(
      surface: palette.bg,
      primary: palette.accent,
    ),
  );
}
