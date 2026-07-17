import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

class _Star {
  const _Star({
    required this.left,
    required this.top,
    required this.size,
    required this.durationSeconds,
    required this.delaySeconds,
  });

  final double left;
  final double top;
  final double size;
  final double durationSeconds;
  final double delaySeconds;
}

/// Ports the design's `starTwinkle` keyframe field: 22 small dots at
/// deterministic pseudo-random positions, each fading in/out and
/// scaling up/down on its own looping period. Positions are generated with
/// the same seed formula as the design's `STAR_FIELD` for visual parity.
List<_Star> _buildStarField() {
  return List.generate(22, (i) {
    final seed = (i * 37.13) % 100;
    return _Star(
      left: (seed * 3.7) % 100 / 100,
      top: (seed * 5.9 + i * 11) % 100 / 100,
      size: (1 + (i % 3)).toDouble(),
      durationSeconds: (4 + (i % 5)).toDouble(),
      delaySeconds: (i * 0.6) % 6,
    );
  });
}

/// Decorative twinkling starfield, absorbed behind the Auth and Home screen
/// content. Purely cosmetic — ignores pointer events.
class StarFieldBackground extends StatefulWidget {
  const StarFieldBackground({super.key});

  @override
  State<StarFieldBackground> createState() => _StarFieldBackgroundState();
}

class _StarFieldBackgroundState extends State<StarFieldBackground> with SingleTickerProviderStateMixin {
  static const _maxOpacity = 0.55;
  final List<_Star> _stars = _buildStarField();
  late final Ticker _ticker;
  Duration _elapsed = Duration.zero;

  @override
  void initState() {
    super.initState();
    _ticker = createTicker((elapsed) => setState(() => _elapsed = elapsed))..start();
  }

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final seconds = _elapsed.inMilliseconds / 1000;
    return IgnorePointer(
      child: LayoutBuilder(
        builder: (context, constraints) {
          return Stack(
            children: _stars.map((star) {
              final phase = ((seconds + star.delaySeconds) % star.durationSeconds) / star.durationSeconds;
              final bell = math.sin(math.pi * phase).clamp(0.0, 1.0);
              return Positioned(
                left: star.left * constraints.maxWidth,
                top: star.top * constraints.maxHeight,
                child: Opacity(
                  opacity: _maxOpacity * bell,
                  child: Transform.scale(
                    scale: 0.6 + 0.4 * bell,
                    child: Container(
                      width: star.size,
                      height: star.size,
                      decoration: const BoxDecoration(color: Color(0xFFEDE7E2), shape: BoxShape.circle),
                    ),
                  ),
                ),
              );
            }).toList(),
          );
        },
      ),
    );
  }
}
