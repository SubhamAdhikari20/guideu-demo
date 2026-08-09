/// A Nepali festival for the information hub, mapped from the core-engine
/// `catalog/events/upcoming` response. Pure domain — no Flutter or JSON.
class Festival {
  const Festival({
    required this.name,
    required this.type,
    required this.significance,
    required this.durationDays,
    required this.badgeEligible,
    required this.badgePoints,
    required this.regions,
  });

  final String name;
  final String type; // Religious | Cultural | Seasonal
  final String significance; // High | Medium | Low
  final int durationDays;
  final bool badgeEligible;
  final int badgePoints;
  final List<String> regions;

  String get durationLabel => durationDays == 1 ? '1 day' : '$durationDays days';

  String get regionLabel =>
      regions.isEmpty ? 'Across Nepal' : regions.join(', ');
}

/// Festivals grouped under a calendar month.
class FestivalMonth {
  const FestivalMonth({
    required this.month,
    required this.monthName,
    required this.festivals,
  });

  final int month; // 1..12
  final String monthName;
  final List<Festival> festivals;
}
