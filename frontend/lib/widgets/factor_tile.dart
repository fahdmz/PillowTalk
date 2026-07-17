import 'package:flutter/material.dart';

import '../models/sleep_factor.dart';

class TranslatedOccurrence {
  const TranslatedOccurrence({required this.label, required this.time});

  final String label;
  final String time;
}

class FactorTile extends StatelessWidget {
  const FactorTile({
    super.key,
    required this.name,
    required this.level,
    required this.levelLabel,
    required this.occurrences,
    required this.loggedDuringLabel,
    required this.expanded,
    required this.onToggle,
    required this.showDivider,
  });

  final String name;
  final FactorLevel level;
  final String levelLabel;
  final List<TranslatedOccurrence> occurrences;
  final String loggedDuringLabel;
  final bool expanded;
  final VoidCallback onToggle;
  final bool showDivider;

  static const _levelStyles = {
    FactorLevel.high: (bg: Color(0x33B06A5A), fg: Color(0xFFE2998A)),
    FactorLevel.medium: (bg: Color(0x2EC08A63), fg: Color(0xFFD9AD82)),
    FactorLevel.low: (bg: Color(0x2E8C7FA3), fg: Color(0xFFB7A6C9)),
  };

  @override
  Widget build(BuildContext context) {
    final style = _levelStyles[level]!;
    return Container(
      decoration: BoxDecoration(
        border: showDivider
            ? const Border(bottom: BorderSide(color: Color(0x0FEDE7E2)))
            : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          InkWell(
            onTap: onToggle,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              child: Row(
                children: [
                  AnimatedRotation(
                    duration: const Duration(milliseconds: 200),
                    turns: expanded ? 0.25 : 0,
                    child: const Icon(Icons.chevron_right, size: 16, color: Color(0x66EDE7E2)),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(name, style: const TextStyle(fontSize: 14, color: Color(0xFFEDE7E2))),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                    decoration: BoxDecoration(color: style.bg, borderRadius: BorderRadius.circular(100)),
                    child: Text(
                      levelLabel,
                      style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700, color: style.fg),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (expanded)
            Padding(
              padding: const EdgeInsets.fromLTRB(27, 0, 16, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(loggedDuringLabel, style: const TextStyle(fontSize: 11, color: Color(0x59EDE7E2))),
                  const SizedBox(height: 8),
                  ...occurrences.map((occ) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
                          decoration: BoxDecoration(
                            color: const Color(0x0AEDE7E2),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(occ.label, style: const TextStyle(fontSize: 12.5, color: Color(0xBFEDE7E2))),
                              Text(occ.time, style: const TextStyle(fontSize: 11, color: Color(0x66EDE7E2))),
                            ],
                          ),
                        ),
                      )),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
