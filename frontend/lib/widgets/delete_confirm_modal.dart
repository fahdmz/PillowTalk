import 'package:flutter/material.dart';

import '../data/strings.dart';
import '../theme/palette.dart';

/// Confirmation prompt shown before a recap entry is actually deleted —
/// mirrors the design's `showDeleteConfirm` layer nested inside the recap
/// detail screen.
class DeleteConfirmModal extends StatelessWidget {
  const DeleteConfirmModal({
    super.key,
    required this.palette,
    required this.t,
    required this.onConfirm,
    required this.onCancel,
  });

  final Palette palette;
  final UiStrings t;
  final VoidCallback onConfirm;
  final VoidCallback onCancel;

  static const _danger = Color(0xFFE05A5A);

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0x8C0A0810),
      alignment: Alignment.center,
      padding: const EdgeInsets.all(24),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 290),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.fromLTRB(20, 24, 20, 18),
          decoration: BoxDecoration(color: palette.card, borderRadius: BorderRadius.circular(22)),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 46,
                height: 46,
                margin: const EdgeInsets.only(bottom: 6),
                decoration: BoxDecoration(color: _danger.withOpacity(0.15), borderRadius: BorderRadius.circular(14)),
                child: const Icon(Icons.delete_outline, color: _danger, size: 19),
              ),
              Text(
                t.deleteEntryTitle,
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: palette.text),
              ),
              const SizedBox(height: 4),
              Text(
                t.deleteEntryBody,
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 13, height: 1.5, color: palette.sub),
              ),
              const SizedBox(height: 12),
              Column(
                children: [
                  GestureDetector(
                    onTap: onConfirm,
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 13),
                      decoration: BoxDecoration(color: _danger, borderRadius: BorderRadius.circular(100)),
                      child: Text(
                        t.deleteEntryConfirm,
                        textAlign: TextAlign.center,
                        style: const TextStyle(fontSize: 14.5, fontWeight: FontWeight.w700, color: Colors.white),
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  GestureDetector(
                    onTap: onCancel,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 11),
                      child: Text(
                        t.deleteEntryCancel,
                        textAlign: TextAlign.center,
                        style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600, color: palette.sub),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
