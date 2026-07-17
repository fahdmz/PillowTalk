import 'package:flutter/material.dart';

import '../data/strings.dart';
import '../theme/palette.dart';

/// The first-time "Allow Microphone Access" prompt, shown once before the
/// first voice check-in recording — mirrors the design's `showMicPermModal`.
class MicPermissionModal extends StatelessWidget {
  const MicPermissionModal({
    super.key,
    required this.palette,
    required this.t,
    required this.onAllow,
    required this.onDeny,
  });

  final Palette palette;
  final UiStrings t;
  final VoidCallback onAllow;
  final VoidCallback onDeny;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0x8C0A0810),
      alignment: Alignment.center,
      padding: const EdgeInsets.all(24),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 300),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.fromLTRB(22, 26, 22, 20),
          decoration: BoxDecoration(color: palette.card, borderRadius: BorderRadius.circular(24)),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 52,
                height: 52,
                margin: const EdgeInsets.only(bottom: 6),
                decoration: BoxDecoration(color: palette.accent, borderRadius: BorderRadius.circular(16)),
                child: Icon(Icons.mic_none_rounded, color: palette.text, size: 24),
              ),
              Text(
                t.micPermTitle,
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16.5, fontWeight: FontWeight.w700, color: palette.text),
              ),
              const SizedBox(height: 4),
              Text(
                t.micPermBody,
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 13, height: 1.5, color: palette.sub),
              ),
              const SizedBox(height: 14),
              SizedBox(
                width: double.infinity,
                child: Column(
                  children: [
                    GestureDetector(
                      onTap: onAllow,
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 13),
                        decoration: BoxDecoration(color: palette.accent, borderRadius: BorderRadius.circular(100)),
                        child: Text(
                          t.micPermAllow,
                          textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 14.5, fontWeight: FontWeight.w700, color: palette.text),
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    GestureDetector(
                      onTap: onDeny,
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 11),
                        child: Text(
                          t.micPermDeny,
                          textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600, color: palette.sub),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
