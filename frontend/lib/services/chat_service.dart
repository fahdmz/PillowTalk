import '../models/chat_message.dart';
import 'api_client.dart';

class StartedSession {
  StartedSession({
    required this.sessionId,
    required this.sessionStatus,
    required this.messages,
  });

  final String sessionId;

  /// 'active' (can keep chatting) or 'completed' (today's check-in of this
  /// type already ran to completion — this is a read-only history).
  final String sessionStatus;

  /// Full conversation so far: just the greeting for a brand-new session,
  /// or the whole history when resuming one already in progress today.
  final List<ChatMessage> messages;
}

class SendMessageResult {
  SendMessageResult({
    required this.userMessage,
    required this.aiMessage,
    required this.sessionCompleted,
  });

  final ChatMessage userMessage;
  final ChatMessage aiMessage;
  final bool sessionCompleted;
}

/// Talks to the fixed-step check-in state machine on the backend — this
/// service never decides what to say next, it just relays the backend's
/// question order and the rule-based crisis reply when it fires.
class ChatService {
  ChatService(this._api);

  final ApiClient _api;

  Future<StartedSession> startSession({
    required String checkinMode,
    required String language,
  }) async {
    final json = await _api.post('/chat/start', body: {
      'checkin_mode': checkinMode,
      'language': language,
      // The backend decides "today" using this offset so a check-in
      // resumes/resets at the user's actual local midnight, not the
      // server's UTC one.
      'timezone_offset_minutes': DateTime.now().timeZoneOffset.inMinutes,
    }) as Map<String, dynamic>;
    final messages = (json['messages'] as List)
        .map((m) => _messageFromJson(m as Map<String, dynamic>))
        .toList();
    return StartedSession(
      sessionId: json['session_id'] as String,
      sessionStatus: json['session_status'] as String,
      messages: messages,
    );
  }

  Future<SendMessageResult> sendMessage({
    required String sessionId,
    required String text,
    required String language,
  }) async {
    final json = await _api.post('/chat/message', body: {
      'session_id': sessionId,
      'text': text,
      'language': language,
    }) as Map<String, dynamic>;
    return SendMessageResult(
      userMessage: _messageFromJson(json['user_message'] as Map<String, dynamic>),
      aiMessage: _messageFromJson(json['ai_message'] as Map<String, dynamic>),
      sessionCompleted: json['session_status'] == 'completed',
    );
  }

  Future<void> endSessionEarly(String sessionId) {
    return _api.post('/chat/$sessionId/end');
  }

  ChatMessage _messageFromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id'] as String,
      sender: json['sender'] == 'ai' ? MessageSender.ai : MessageSender.user,
      text: json['text'] as String?,
      isCrisis: json['is_crisis'] as bool? ?? false,
      crisisPrefix: json['crisis_prefix'] as String?,
      crisisPhone: json['crisis_phone'] as String?,
      crisisSuffix: json['crisis_suffix'] as String?,
    );
  }
}
