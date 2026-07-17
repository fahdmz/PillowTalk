import 'package:flutter/material.dart';

/// The pill-shaped, drop-shadowed primary call-to-action button used on
/// the auth screen.
class PrimaryButton extends StatelessWidget {
  const PrimaryButton({
    super.key,
    required this.label,
    required this.onTap,
    this.color = const Color(0xFF392A48),
    this.textColor = const Color(0xFFEDE7E2),
  });

  final String label;
  final VoidCallback onTap;
  final Color color;
  final Color textColor;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(100),
          boxShadow: [
            BoxShadow(color: color.withOpacity(0.5), blurRadius: 24, offset: const Offset(0, 8)),
          ],
        ),
        child: Text(
          label,
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: textColor, letterSpacing: 0.2),
        ),
      ),
    );
  }
}
