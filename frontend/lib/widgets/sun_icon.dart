import 'dart:math' as math;

import 'package:flutter/material.dart';

/// A filled circle with radiating rays, recreating the design's sun SVG.
class SunIcon extends StatelessWidget {
  const SunIcon({super.key, required this.color, this.size = 20, this.rayCount = 8});

  final Color color;
  final double size;
  final int rayCount;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size.square(size),
      painter: _SunPainter(color, rayCount),
    );
  }
}

class _SunPainter extends CustomPainter {
  _SunPainter(this.color, this.rayCount);

  final Color color;
  final int rayCount;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final coreRadius = size.width * 0.22;
    canvas.drawCircle(center, coreRadius, Paint()..color = color);

    final rayPaint = Paint()
      ..color = color
      ..strokeWidth = size.width * 0.08
      ..strokeCap = StrokeCap.round;
    final rayInner = size.width * 0.38;
    final rayOuter = size.width * 0.5;
    for (var i = 0; i < rayCount; i++) {
      final angle = (2 * math.pi / rayCount) * i;
      final from = center + Offset(math.cos(angle), math.sin(angle)) * rayInner;
      final to = center + Offset(math.cos(angle), math.sin(angle)) * rayOuter;
      canvas.drawLine(from, to, rayPaint);
    }
  }

  @override
  bool shouldRepaint(covariant _SunPainter oldDelegate) =>
      oldDelegate.color != color || oldDelegate.rayCount != rayCount;
}
