import 'chat_message.dart';

class RecapEntry {
  RecapEntry({
    required this.id,
    required this.date,
    required this.time,
    required this.isNight,
    required this.preview,
    this.title,
    this.summary,
    this.transcript = const [],
  });

  final String id;
  final DateTime date;
  final String time;
  final bool isNight;
  final String preview;
  final String? title;
  final String? summary;

  /// Empty until [openRecapEntry] lazily fetches the full transcript from
  /// `GET /recaps/:id` — the list endpoint only returns a preview.
  List<ChatMessage> transcript;
}

/// A date-label key into [DateLabelTranslations] — mirrors the design's
/// `dateLabel` values ('Today', 'Yesterday', 'Monday', 'Last week').
class RecapGroup {
  RecapGroup({
    required this.dateLabelKey,
    required this.dateValue,
    required this.items,
  });

  final String dateLabelKey;
  final DateTime dateValue;
  final List<RecapEntry> items;
}
