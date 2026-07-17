import 'package:flutter/material.dart';

/// The soft pulsing radial glow behind "Ready to check in?", matching the
/// design's `breathe` keyframe animation (5s ease-in-out, scale + opacity).
class BreathingCircle extends StatefulWidget {
  const BreathingCircle({super.key, this.color = const Color(0xFF6B5484)});

  final Color color;

  @override
  State<BreathingCircle> createState() => _BreathingCircleState();
}

class _BreathingCircleState extends State<BreathingCircle> with SingleTickerProviderStateMixin {
  late final AnimationController _controller =
      AnimationController(vsync: this, duration: const Duration(seconds: 5))..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final curved = Curves.easeInOut.transform(_controller.value);
        final scale = 1.0 + 0.15 * curved;
        final opacity = 0.5 + 0.35 * curved;
        return Opacity(
          opacity: opacity,
          child: Transform.scale(
            scale: scale,
            child: Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [widget.color.withOpacity(0.35), widget.color.withOpacity(0)],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
