import 'package:flutter/material.dart';

/// A single standalone rounded filter chip (used for the recap
/// All/Nightly/Morning row) — visually distinct from [SegmentedToggle],
/// which shares one background across all of its options.
class FilterPill extends StatelessWidget {
  const FilterPill({
    super.key,
    required this.label,
    required this.selected,
    required this.onTap,
    required this.activeColor,
    required this.activeTextColor,
    required this.inactiveColor,
    required this.inactiveTextColor,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;
  final Color activeColor;
  final Color activeTextColor;
  final Color inactiveColor;
  final Color inactiveTextColor;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? activeColor : inactiveColor,
          borderRadius: BorderRadius.circular(100),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12.5,
            color: selected ? activeTextColor : inactiveTextColor,
          ),
        ),
      ),
    );
  }
}
