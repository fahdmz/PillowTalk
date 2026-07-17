import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../state/app_state.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/mic_permission_modal.dart';
import '../widgets/typing_indicator.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _draftController = TextEditingController();

  @override
  void dispose() {
    _scrollController.dispose();
    _draftController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    if (!_scrollController.hasClients) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    final palette = app.palette;
    final t = app.t;
    final isMorning = app.checkinMode == CheckinMode.morning;

    if (_draftController.text != app.draft) {
      _draftController.value = _draftController.value.copyWith(
        text: app.draft,
        selection: TextSelection.collapsed(offset: app.draft.length),
      );
    }
    _scrollToBottom();

    return AnimatedContainer(
      duration: const Duration(milliseconds: 500),
      color: palette.bg,
      child: Stack(
        children: [
          Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 56, 20, 16),
            child: Row(
              children: [
                GestureDetector(
                  onTap: app.exitChat,
                  child: Container(
                    width: 34,
                    height: 34,
                    decoration: BoxDecoration(color: palette.card, shape: BoxShape.circle),
                    child: Icon(Icons.close, size: 16, color: palette.sub),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        isMorning ? t.morningCheckin : t.nightlyCheckin,
                        style: TextStyle(fontSize: 15.5, fontWeight: FontWeight.w700, color: palette.text),
                      ),
                      Text(
                        t.listeningNoJudgment,
                        style: TextStyle(fontSize: 11.5, color: palette.sub),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Container(height: 1, color: palette.divider),
          Expanded(
            child: ListView.separated(
              controller: _scrollController,
              padding: const EdgeInsets.all(18),
              itemCount: app.messages.length + (app.aiTyping ? 1 : 0),
              separatorBuilder: (context, index) => const SizedBox(height: 14),
              itemBuilder: (context, index) {
                if (index == app.messages.length) {
                  return TypingIndicator(dotColor: palette.sub, bubbleColor: palette.card);
                }
                return ChatBubble(message: app.messages[index], palette: palette);
              },
            ),
          ),
          Container(height: 1, color: palette.divider),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 26),
            child: Column(
              children: [
                if (app.isRecording) ...[
                  Text(t.listening, style: TextStyle(fontSize: 12.5, color: palette.sub)),
                  const SizedBox(height: 10),
                ],
                Text(
                  app.inputMode == InputMode.stt ? t.voiceInputCaption : t.aiVoiceCaption,
                  style: TextStyle(fontSize: 10.5, color: palette.sub),
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(color: palette.card, borderRadius: BorderRadius.circular(100)),
                  child: Row(
                    children: [
                      GestureDetector(
                        onTap: app.toggleInputMode,
                        child: Container(
                          width: 38,
                          height: 38,
                          decoration: BoxDecoration(
                            color: app.inputMode == InputMode.tts ? palette.accent : Colors.transparent,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            app.inputMode == InputMode.tts ? Icons.volume_up_rounded : Icons.volume_off_rounded,
                            size: 18,
                            color: app.inputMode == InputMode.tts ? Colors.white : palette.sub,
                          ),
                        ),
                      ),
                      Expanded(
                        child: TextField(
                          controller: _draftController,
                          onChanged: app.updateDraft,
                          onSubmitted: (_) => app.sendMessage(),
                          textInputAction: TextInputAction.send,
                          style: TextStyle(fontSize: 14.5, color: palette.text),
                          decoration: InputDecoration(
                            hintText: t.typeOrSpeak,
                            hintStyle: TextStyle(color: palette.sub),
                            border: InputBorder.none,
                            contentPadding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
                          ),
                        ),
                      ),
                      GestureDetector(
                        onTap: app.draft.trim().isNotEmpty ? () => app.sendMessage() : app.startVoiceInput,
                        child: Container(
                          width: 38,
                          height: 38,
                          decoration: BoxDecoration(
                            color: app.draft.trim().isNotEmpty ? palette.accent : palette.cardAlt,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            app.draft.trim().isNotEmpty ? Icons.arrow_upward_rounded : Icons.mic_rounded,
                            size: app.draft.trim().isNotEmpty ? 18 : 16,
                            color: app.draft.trim().isNotEmpty ? Colors.white : palette.sub,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
          ),
          if (app.showMicPermModal)
            Positioned.fill(
              child: MicPermissionModal(
                palette: palette,
                t: t,
                onAllow: app.allowMicPerm,
                onDeny: app.denyMicPerm,
              ),
            ),
        ],
      ),
    );
  }
}
