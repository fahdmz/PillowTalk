import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../state/app_state.dart';
import '../../widgets/breathing_circle.dart';
import '../../widgets/crescent_moon_icon.dart';
import '../../widgets/sun_icon.dart';

class CheckinTab extends StatelessWidget {
  const CheckinTab({super.key});

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    final t = app.t;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SizedBox(
          height: 150,
          child: Stack(
            alignment: Alignment.topCenter,
            children: [
              const Padding(padding: EdgeInsets.only(top: 6), child: BreathingCircle()),
              Padding(
                padding: const EdgeInsets.only(top: 30),
                child: Column(
                  children: [
                    Text(
                      t.readyCheckin,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: Color(0xFFEDE7E2)),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      t.chooseMoment,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 13, color: Color(0x73EDE7E2)),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 6),
        _CheckinCard(
          background: const Color(0xFF1F1B2E),
          iconBg: const Color(0xFF392A48),
          icon: const CrescentMoonIcon(color: Color(0xFFEDE7E2), size: 24),
          title: t.nightlyCheckin,
          subtitle: t.windDown,
          onTap: () => app.selectCheckin(CheckinMode.night),
        ),
        const SizedBox(height: 16),
        _CheckinCard(
          background: const Color(0xFF241F33),
          iconBg: const Color(0xFFC08A63),
          icon: const SunIcon(color: Color(0xFF2A1F16), size: 22, rayCount: 8),
          title: t.morningCheckin,
          subtitle: t.reflect,
          onTap: () => app.selectCheckin(CheckinMode.morning),
        ),
      ],
    );
  }
}

class _CheckinCard extends StatelessWidget {
  const _CheckinCard({
    required this.background,
    required this.iconBg,
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final Color background;
  final Color iconBg;
  final Widget icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: background,
      borderRadius: BorderRadius.circular(22),
      child: InkWell(
        borderRadius: BorderRadius.circular(22),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: const Color(0x0DFFFFFF)),
          ),
          child: Row(
            children: [
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(color: iconBg, borderRadius: BorderRadius.circular(16)),
                child: Center(child: icon),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Color(0xFFEDE7E2))),
                    const SizedBox(height: 3),
                    Text(subtitle, style: const TextStyle(fontSize: 12.5, color: Color(0x73EDE7E2))),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, size: 16, color: Color(0x59EDE7E2)),
            ],
          ),
        ),
      ),
    );
  }
}
