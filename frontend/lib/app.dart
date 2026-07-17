import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'screens/auth_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/home_screen.dart';
import 'state/app_state.dart';
import 'theme/app_theme.dart';
import 'theme/bedtime_filter.dart';
import 'theme/palette.dart';

class DrowzyDiaryApp extends StatelessWidget {
  const DrowzyDiaryApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AppState(),
      child: Builder(
        builder: (context) {
          final app = context.watch<AppState>();
          return MaterialApp(
            title: 'DrowzyDiary',
            debugShowCheckedModeBanner: false,
            theme: buildAppTheme(Palette.night),
            home: _BedtimeFilter(
              enabled: app.bedtimeMode,
              child: const _ScreenSwitcher(),
            ),
          );
        },
      ),
    );
  }
}

class _BedtimeFilter extends StatelessWidget {
  const _BedtimeFilter({required this.enabled, required this.child});

  final bool enabled;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    if (!enabled) return child;
    return ColorFiltered(colorFilter: bedtimeColorFilter, child: child);
  }
}

class _ScreenSwitcher extends StatelessWidget {
  const _ScreenSwitcher();

  @override
  Widget build(BuildContext context) {
    final screen = context.select((AppState app) => app.screen);
    return Scaffold(
      body: SafeArea(
        top: false,
        bottom: false,
        child: switch (screen) {
          AppScreen.auth => const AuthScreen(),
          AppScreen.home => const HomeScreen(),
          AppScreen.chat => const ChatScreen(),
        },
      ),
    );
  }
}
