import 'package:flutter/material.dart';

class SegmentOption {
  const SegmentOption({required this.label, required this.onTap, required this.selected});

  final String label;
  final VoidCallback onTap;
  final bool selected;
}

/// A pill-shaped multi-segment toggle sharing one rounded background —
/// used for the auth Log In/Sign Up switch and the EN/ID language switch.
class SegmentedToggle extends StatelessWidget {
  const SegmentedToggle({
    super.key,
    required this.options,
    required this.activeColor,
    required this.activeTextColor,
    required this.inactiveTextColor,
    this.trackColor = const Color(0x0DFFFFFF),
    this.expand = true,
    this.segmentPadding = const EdgeInsets.symmetric(vertical: 11),
    this.fontSize = 14,
  });

  final List<SegmentOption> options;
  final Color activeColor;
  final Color activeTextColor;
  final Color inactiveTextColor;
  final Color trackColor;
  final bool expand;
  final EdgeInsets segmentPadding;
  final double fontSize;

  @override
  Widget build(BuildContext context) {
    final children = options.map((option) {
      final segment = AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        padding: segmentPadding,
        decoration: BoxDecoration(
          color: option.selected ? activeColor : Colors.transparent,
          borderRadius: BorderRadius.circular(100),
        ),
        child: Text(
          option.label,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: fontSize,
            fontWeight: FontWeight.w600,
            color: option.selected ? activeTextColor : inactiveTextColor,
          ),
        ),
      );
      final tappable = GestureDetector(onTap: option.onTap, child: segment);
      return expand ? Expanded(child: tappable) : tappable;
    }).toList();

    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(color: trackColor, borderRadius: BorderRadius.circular(100)),
      child: Row(mainAxisSize: expand ? MainAxisSize.max : MainAxisSize.min, children: children),
    );
  }
}
