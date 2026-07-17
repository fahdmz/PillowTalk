import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../data/strings.dart';
import '../state/app_state.dart';
import '../theme/palette.dart';
import '../widgets/chat_bubble.dart';

/// Slide-in overlay showing a past check-in's full transcript, matching the
/// design's `showRecapDetail` layer (absolute, z-index above the home tabs).
class RecapDetailScreen extends StatefulWidget {
  const RecapDetailScreen({super.key});

  @override
  State<RecapDetailScreen> createState() => _RecapDetailScreenState();
}

class _RecapDetailScreenState extends State<RecapDetailScreen> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 320),
  )..forward();
  late final Animation<Offset> _slide = Tween<Offset>(
    begin: const Offset(0.12, 0),
    end: Offset.zero,
  ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic));

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    final open = app.openEntry;
    if (open == null) return const SizedBox.shrink();

    final palette = open.entry.isNight ? Palette.night : Palette.morning;
    final dateLabel = dateLabelTranslations[app.lang]![open.dateLabelKey] ?? open.dateLabelKey;

    return SlideTransition(
      position: _slide,
      child: FadeTransition(
        opacity: _controller,
        child: Container(
          color: palette.bg,
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 56, 20, 16),
                child: Row(
                  children: [
                    GestureDetector(
                      onTap: app.closeRecapDetail,
                      child: Container(
                        width: 34,
                        height: 34,
                        decoration: BoxDecoration(color: palette.card, shape: BoxShape.circle),
                        child: Icon(Icons.chevron_left, size: 18, color: palette.sub),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(dateLabel, style: TextStyle(fontSize: 15.5, fontWeight: FontWeight.w700, color: palette.text)),
                          Text(open.entry.time, style: TextStyle(fontSize: 11.5, color: palette.sub)),
                        ],
                      ),
                    ),
                    GestureDetector(
                      onTap: app.deleteEntry,
                      child: Container(
                        width: 34,
                        height: 34,
                        decoration: BoxDecoration(color: palette.card, shape: BoxShape.circle),
                        child: Icon(Icons.delete_outline, size: 16, color: palette.sub),
                      ),
                    ),
                  ],
                ),
              ),
              Container(height: 1, color: palette.divider),
              Expanded(
                child: ListView.separated(
                  padding: const EdgeInsets.all(18),
                  itemCount: open.entry.transcript.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 14),
                  itemBuilder: (context, index) => ChatBubble(message: open.entry.transcript[index], palette: palette),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
