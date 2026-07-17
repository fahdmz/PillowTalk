import 'package:flutter/material.dart';

/// A filled circle with a smaller offset circle cut out, producing a
/// crescent — recreates the design's SVG `<mask>` moon icon regardless of
/// what's behind it (uses [BlendMode.dstOut] rather than a fixed background
/// color punch-out).
class CrescentMoonIcon extends StatelessWidget {
  const CrescentMoonIcon({super.key, required this.color, this.size = 20});

  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size.square(size),
      painter: _CrescentPainter(color),
    );
  }
}

class _CrescentPainter extends CustomPainter {
  _CrescentPainter(this.color);

  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final layerBounds = Rect.fromLTWH(0, 0, size.width, size.height);
    canvas.saveLayer(layerBounds, Paint());

    final mainRadius = size.width * 0.4;
    final mainCenter = Offset(size.width * 0.5, size.height * 0.5);
    canvas.drawCircle(mainCenter, mainRadius, Paint()..color = color);

    final cutRadius = size.width * 0.35;
    final cutCenter = Offset(size.width * 0.7, size.height * 0.35);
    canvas.drawCircle(
      cutCenter,
      cutRadius,
      Paint()..blendMode = BlendMode.dstOut,
    );

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _CrescentPainter oldDelegate) => oldDelegate.color != color;
}
