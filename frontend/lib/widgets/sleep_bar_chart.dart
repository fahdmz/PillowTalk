import 'package:flutter/material.dart';

class SleepBarChart extends StatelessWidget {
  const SleepBarChart({super.key, required this.hoursByDay, required this.dayLabels});

  final List<double> hoursByDay;
  final List<String> dayLabels;

  static const _lowSleepColor = Color(0xFFB06A5A);
  static const _goodSleepColor = Color(0xFF8C7FA3);

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SizedBox(
          height: 100,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: List.generate(hoursByDay.length, (i) {
              final hours = hoursByDay[i];
              final pct = (hours / 9).clamp(0.0, 1.0);
              return Expanded(
                child: Padding(
                  padding: EdgeInsets.only(right: i == hoursByDay.length - 1 ? 0 : 8),
                  child: Align(
                    alignment: Alignment.bottomCenter,
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 500),
                      height: (100 * pct).clamp(4, 100),
                      decoration: BoxDecoration(
                        color: hours < 7 ? _lowSleepColor : _goodSleepColor,
                        borderRadius: const BorderRadius.vertical(
                          top: Radius.circular(6),
                          bottom: Radius.circular(3),
                        ),
                      ),
                    ),
                  ),
                ),
              );
            }),
          ),
        ),
        const SizedBox(height: 10),
        Row(
          children: dayLabels
              .map((d) => Expanded(
                    child: Text(
                      d,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 11, color: Color(0x66EDE7E2)),
                    ),
                  ))
              .toList(),
        ),
      ],
    );
  }
}
