import 'package:flutter/material.dart';

import '../data/strings.dart';
import '../state/app_state.dart';
import '../widgets/crescent_moon_icon.dart';
import '../widgets/sun_icon.dart';

/// A fake system-notification banner used to preview what the night/morning
/// check-in reminder looks like. Slides down from off-screen when open,
/// tapping it deep-links into that check-in (like tapping a real push
/// notification would) — mirrors the design's `notifOpen`/`notifTransform`.
class NotificationBanner extends StatelessWidget {
  const NotificationBanner({
    super.key,
    required this.open,
    required this.type,
    required this.t,
    required this.onTap,
    required this.onDismiss,
  });

  final bool open;
  final CheckinMode? type;
  final UiStrings t;
  final VoidCallback onTap;
  final VoidCallback onDismiss;

  @override
  Widget build(BuildContext context) {
    final isNight = type != CheckinMode.morning;
    final title = type == CheckinMode.morning ? t.notifMorningTitle : t.notifNightTitle;
    final body = type == CheckinMode.morning ? t.notifMorningBody : t.notifNightBody;
    final iconBg = type == CheckinMode.morning ? const Color(0xFFC08A63) : const Color(0xFF392A48);
    final iconColor = type == CheckinMode.morning ? const Color(0xFF2A1F16) : const Color(0xFFEDE7E2);

    return AnimatedPositioned(
      duration: const Duration(milliseconds: 500),
      curve: Curves.easeOutCubic,
      top: open ? 54 : -160,
      left: 12,
      right: 12,
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: const Color(0xEB1C1828),
            border: Border.all(color: const Color(0x17FFFFFF)),
            borderRadius: BorderRadius.circular(20),
            boxShadow: const [BoxShadow(color: Color(0x66000000), blurRadius: 34, offset: Offset(0, 16))],
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(color: iconBg, borderRadius: BorderRadius.circular(10)),
                child: Center(
                  child: isNight
                      ? CrescentMoonIcon(color: iconColor, size: 17)
                      : SunIcon(color: iconColor, size: 16, rayCount: 8),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Text(
                          'DrowzyDiary',
                          style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700, color: Color(0xFFEDE7E2)),
                        ),
                        const SizedBox(width: 6),
                        Text(t.notifNow, style: const TextStyle(fontSize: 11.5, color: Color(0x66EDE7E2))),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      title,
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFFEDE7E2)),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      body,
                      style: const TextStyle(fontSize: 12.5, height: 1.4, color: Color(0x99EDE7E2)),
                    ),
                  ],
                ),
              ),
              GestureDetector(
                onTap: onDismiss,
                child: Container(
                  width: 22,
                  height: 22,
                  decoration: BoxDecoration(color: const Color(0x14FFFFFF), shape: BoxShape.circle),
                  child: const Icon(Icons.close, size: 11, color: Color(0x80EDE7E2)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
