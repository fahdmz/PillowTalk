import '../models/chat_message.dart';
import 'api_client.dart';

class StartedSession {
  StartedSession({required this.sessionId, required this.greeting});

  final String sessionId;
  final ChatMessage greeting;
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
    }) as Map<String, dynamic>;
    return StartedSession(
      sessionId: json['session_id'] as String,
      greeting: _messageFromJson(json['greeting'] as Map<String, dynamic>),
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
