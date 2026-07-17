enum FactorLevel { high, medium, low }

class SleepOccurrence {
  const SleepOccurrence({required this.checkinLabelKey, required this.time});

  /// Key into [CheckinLabelTranslations] ('Nightly Check-in' / 'Morning Check-in').
  final String checkinLabelKey;
  final String time;
}

class SleepFactor {
  const SleepFactor({
    required this.nameKey,
    required this.level,
    required this.occurrences,
  });

  /// Key into [FactorNameTranslations].
  final String nameKey;
  final FactorLevel level;
  final List<SleepOccurrence> occurrences;
}
