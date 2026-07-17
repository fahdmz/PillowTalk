import 'package:flutter/material.dart';

/// Three dots bouncing out of phase, matching the design's
/// `typingBounce` keyframe animation staggered by 0.15s per dot.
class TypingIndicator extends StatefulWidget {
  const TypingIndicator({super.key, required this.dotColor, required this.bubbleColor});

  final Color dotColor;
  final Color bubbleColor;

  @override
  State<TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<TypingIndicator> with SingleTickerProviderStateMixin {
  late final AnimationController _controller =
      AnimationController(vsync: this, duration: const Duration(milliseconds: 1000))..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        decoration: BoxDecoration(color: widget.bubbleColor, borderRadius: BorderRadius.circular(18)),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (i) => _dot(i * 0.15)),
        ),
      ),
    );
  }

  Widget _dot(double delayFraction) {
    return Padding(
      padding: EdgeInsets.only(right: delayFraction == 0.3 ? 0 : 5),
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          final t = (_controller.value + delayFraction) % 1.0;
          final bounce = t < 0.5 ? t / 0.5 : (1 - t) / 0.5;
          return Transform.translate(
            offset: Offset(0, -5 * bounce),
            child: child,
          );
        },
        child: Container(
          width: 7,
          height: 7,
          decoration: BoxDecoration(color: widget.dotColor, shape: BoxShape.circle),
        ),
      ),
    );
  }
}
