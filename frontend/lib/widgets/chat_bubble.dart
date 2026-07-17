import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/chat_message.dart';
import '../theme/palette.dart';

class ChatBubble extends StatelessWidget {
  const ChatBubble({super.key, required this.message, required this.palette});

  final ChatMessage message;
  final Palette palette;

  @override
  Widget build(BuildContext context) {
    final isUser = message.sender == MessageSender.user;
    final bg = message.isCrisis
        ? Palette.crisisBubble
        : (isUser ? palette.userBubble : palette.card);

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
          decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(18)),
          child: message.isCrisis ? _crisisText() : _plainText(),
        ),
      ),
    );
  }

  Widget _plainText() {
    return Text(
      message.text ?? '',
      style: TextStyle(fontSize: 14.5, height: 1.55, color: palette.text),
    );
  }

  Widget _crisisText() {
    return RichText(
      text: TextSpan(
        style: TextStyle(fontSize: 14.5, height: 1.55, color: palette.text),
        children: [
          TextSpan(text: message.crisisPrefix ?? ''),
          TextSpan(
            text: message.crisisPhone ?? '',
            style: const TextStyle(fontWeight: FontWeight.w800, decoration: TextDecoration.underline),
            recognizer: TapGestureRecognizer()
              ..onTap = () => launchUrl(Uri.parse('tel:119')),
          ),
          TextSpan(text: message.crisisSuffix ?? ''),
        ],
      ),
    );
  }
}
