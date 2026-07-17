import '../models/chat_message.dart';
import 'api_client.dart';

class RecapListItem {
  RecapListItem({
    required this.id,
    required this.date,
    required this.time,
    required this.isNight,
    this.preview,
  });

  final String id;
  final DateTime date;
  final String time;
  final bool isNight;
  final String? preview;

  factory RecapListItem.fromJson(Map<String, dynamic> json) {
    return RecapListItem(
      id: json['id'] as String,
      date: DateTime.parse(json['date'] as String),
      time: json['time'] as String,
      isNight: json['is_night'] as bool,
      preview: json['preview'] as String?,
    );
  }
}

class RecapDetail {
  RecapDetail({required this.id, required this.transcript});

  final String id;
  final List<ChatMessage> transcript;
}

class RecapService {
  RecapService(this._api);

  final ApiClient _api;

  Future<List<RecapListItem>> listRecaps({String filter = 'all', String? month}) async {
    final json = await _api.get('/recaps', query: {
      'filter': filter,
      if (month != null) 'month': month,
    }) as List;
    return json.map((e) => RecapListItem.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<RecapDetail> getRecap(String id) async {
    final json = await _api.get('/recaps/$id') as Map<String, dynamic>;
    final transcript = (json['transcript'] as List)
        .map((m) => _messageFromJson(m as Map<String, dynamic>))
        .toList();
    return RecapDetail(id: json['id'] as String, transcript: transcript);
  }

  Future<void> deleteRecap(String id) => _api.delete('/recaps/$id');

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
