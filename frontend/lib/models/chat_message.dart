enum MessageSender { ai, user }

/// A single chat turn. Crisis messages carry a split prefix/phone/suffix so
/// the UI can render the crisis phone number as a tappable `tel:` link,
/// mirroring the design's `dmsg.crisisPrefix` / `crisisPhone` / `crisisSuffix`.
class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.sender,
    this.text,
    this.isCrisis = false,
    this.crisisPrefix,
    this.crisisPhone,
    this.crisisSuffix,
  });

  final Object id;
  final MessageSender sender;
  final String? text;
  final bool isCrisis;
  final String? crisisPrefix;
  final String? crisisPhone;
  final String? crisisSuffix;
}
