import '../models/language.dart';

const _shortMonthsEn = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];
const _shortMonthsId = [
  'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
  'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des',
];
const _fullMonthsEn = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];
const _fullMonthsId = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
];

/// "Jul 14" / "14 Jul" style short date, matching the design's
/// `toLocaleDateString(locale, { month: 'short', day: 'numeric' })`.
String formatShortDate(DateTime date, AppLanguage lang) {
  final months = lang == AppLanguage.en ? _shortMonthsEn : _shortMonthsId;
  return '${months[date.month - 1]} ${date.day}';
}

/// "July 2026" style month label for the recap month filter.
String formatMonthYear(DateTime date, AppLanguage lang) {
  final months = lang == AppLanguage.en ? _fullMonthsEn : _fullMonthsId;
  return '${months[date.month - 1]} ${date.year}';
}

/// Numeric slash-form date for the recap detail header — "7/17/2026"
/// (month/day/year) in English, "17/7/2026" (day/month/year) in Indonesian.
String formatSlashDate(DateTime date, AppLanguage lang) {
  return lang == AppLanguage.en
      ? '${date.month}/${date.day}/${date.year}'
      : '${date.day}/${date.month}/${date.year}';
}

const _weekdaysEn = [
  'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
];

/// Whether a recap group's `dateLabelKey` is a bare weekday name (as opposed
/// to 'Today' / 'Yesterday' / 'Last week') — these need a date suffix since
/// the same weekday name recurs every 7 days.
bool isWeekdayLabelKey(String key) => _weekdaysEn.contains(key);

/// Buckets a date into the Recap tab's grouping keys: 'Today', 'Yesterday',
/// an English weekday name if within the last week, else 'Last week' —
/// mirrors how the design's seed data was hand-grouped, but computed from a
/// real date so it works for backend-returned recaps too.
String recapDateLabelKey(DateTime date, {DateTime? now}) {
  final today = now ?? DateTime.now();
  final startOfToday = DateTime(today.year, today.month, today.day);
  final startOfDate = DateTime(date.year, date.month, date.day);
  final daysAgo = startOfToday.difference(startOfDate).inDays;
  if (daysAgo == 0) return 'Today';
  if (daysAgo == 1) return 'Yesterday';
  if (daysAgo >= 2 && daysAgo <= 6) return _weekdaysEn[date.weekday - 1];
  return 'Last week';
}

/// "Today, 11:42 PM" / "Last week, 11:05 PM" style label for a sleep-factor
/// occurrence timestamp, matching the shape [translateTimeWords] expects.
String formatOccurrenceTime(DateTime date, {DateTime? now}) {
  final labelKey = recapDateLabelKey(date, now: now);
  final hour12 = () {
    final h = date.hour % 12;
    return h == 0 ? 12 : h;
  }();
  final minute = date.minute.toString().padLeft(2, '0');
  final period = date.hour < 12 ? 'AM' : 'PM';
  return '$labelKey, $hour12:$minute $period';
}
