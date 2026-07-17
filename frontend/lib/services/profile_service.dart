import '../models/sleep_factor.dart';
import 'api_client.dart';

class ProfileData {
  ProfileData({
    required this.fullName,
    required this.age,
    required this.language,
    required this.bedtimeMode,
    required this.reminderTone,
    required this.quietHoursStart,
    required this.quietHoursEnd,
  });

  final String? fullName;
  final int? age;
  final String language;
  final bool bedtimeMode;
  final String reminderTone;
  final String quietHoursStart;
  final String quietHoursEnd;

  factory ProfileData.fromJson(Map<String, dynamic> json) {
    return ProfileData(
      fullName: json['full_name'] as String?,
      age: json['age'] as int?,
      language: json['language'] as String? ?? 'en',
      bedtimeMode: json['bedtime_mode'] as bool? ?? false,
      reminderTone: json['reminder_tone'] as String? ?? 'chimes',
      quietHoursStart: json['quiet_hours_start'] as String? ?? '22:00',
      quietHoursEnd: json['quiet_hours_end'] as String? ?? '07:00',
    );
  }
}

class WeeklySleepPoint {
  WeeklySleepPoint({required this.day, required this.hours});

  /// 'Mon'..'Sun'
  final String day;
  final double hours;
}

class SleepStats {
  SleepStats({required this.week, this.avgSleepTime, this.avgWakeTime});

  final List<WeeklySleepPoint> week;
  final String? avgSleepTime;
  final String? avgWakeTime;
}

/// Backend-returned equivalent of [SleepFactor], plus the raw occurrence
/// timestamps (formatted for display by the caller, since that needs the
/// app's current language).
class SleepFactorData {
  SleepFactorData({required this.nameKey, required this.level, required this.occurrences});

  final String nameKey;
  final FactorLevel level;
  final List<SleepOccurrenceData> occurrences;
}

class SleepOccurrenceData {
  SleepOccurrenceData({required this.checkinLabelKey, required this.time});

  final String checkinLabelKey;
  final DateTime time;
}

class ProfileService {
  ProfileService(this._api);

  final ApiClient _api;

  Future<ProfileData> getProfile() async {
    final json = await _api.get('/profile') as Map<String, dynamic>;
    return ProfileData.fromJson(json);
  }

  Future<ProfileData> updateProfile({
    int? age,
    String? language,
    bool? bedtimeMode,
    String? reminderTone,
    String? quietHoursStart,
    String? quietHoursEnd,
  }) async {
    final json = await _api.patch('/profile', body: {
      if (age != null) 'age': age,
      if (language != null) 'language': language,
      if (bedtimeMode != null) 'bedtime_mode': bedtimeMode,
      if (reminderTone != null) 'reminder_tone': reminderTone,
      if (quietHoursStart != null) 'quiet_hours_start': quietHoursStart,
      if (quietHoursEnd != null) 'quiet_hours_end': quietHoursEnd,
    }) as Map<String, dynamic>;
    return ProfileData.fromJson(json);
  }

  Future<SleepStats> getWeeklySleep() async {
    final json = await _api.get(
      '/profile/sleep/weekly',
      query: {'timezone_offset_minutes': '${DateTime.now().timeZoneOffset.inMinutes}'},
    ) as Map<String, dynamic>;
    final week = (json['week'] as List)
        .map((e) => WeeklySleepPoint(day: e['day'] as String, hours: (e['hours'] as num).toDouble()))
        .toList();
    return SleepStats(
      week: week,
      avgSleepTime: json['avg_sleep_time'] as String?,
      avgWakeTime: json['avg_wake_time'] as String?,
    );
  }

  Future<List<SleepFactorData>> getSleepFactors() async {
    final json = await _api.get(
      '/profile/sleep-factors',
      query: {'timezone_offset_minutes': '${DateTime.now().timeZoneOffset.inMinutes}'},
    ) as List;
    return json.map((e) {
      final map = e as Map<String, dynamic>;
      return SleepFactorData(
        nameKey: map['name_key'] as String,
        level: _levelFromString(map['level'] as String),
        occurrences: (map['occurrences'] as List).map((o) {
          final occMap = o as Map<String, dynamic>;
          return SleepOccurrenceData(
            checkinLabelKey: occMap['checkin_label_key'] as String,
            time: DateTime.parse(occMap['time'] as String).toLocal(),
          );
        }).toList(),
      );
    }).toList();
  }

  FactorLevel _levelFromString(String value) {
    switch (value) {
      case 'high':
        return FactorLevel.high;
      case 'medium':
        return FactorLevel.medium;
      default:
        return FactorLevel.low;
    }
  }
}
