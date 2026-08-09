/// A travel workspace ("trip") the tourist is planning. Pure domain entity.
class TravelTrip {
  const TravelTrip({
    required this.id,
    required this.title,
    required this.startDate,
    required this.endDate,
    required this.totalBudgetNpr,
    required this.currencyPreference,
    required this.itemCount,
    required this.totalPlannedCostNpr,
    required this.tripDays,
    this.notes = '',
    this.items = const [],
  });

  final int id;
  final String title;
  final DateTime startDate;
  final DateTime endDate;
  final double totalBudgetNpr;
  final String currencyPreference;
  final int itemCount;
  final double totalPlannedCostNpr;
  final int tripDays;
  final String notes;
  final List<TripItem> items;

  double get remainingNpr => totalBudgetNpr - totalPlannedCostNpr;
  bool get isOverBudget => totalPlannedCostNpr > totalBudgetNpr;

  /// Fraction of budget used, clamped to 0..1 for the progress bar.
  double get budgetFraction {
    if (totalBudgetNpr <= 0) return 0;
    return (totalPlannedCostNpr / totalBudgetNpr).clamp(0, 1).toDouble();
  }
}

/// A single itinerary item within a trip.
class TripItem {
  const TripItem({
    required this.id,
    required this.itemType,
    required this.title,
    required this.dayNumber,
    required this.displayOrder,
    required this.estimatedCostNpr,
    this.isBooked = false,
  });

  final int id;
  final String itemType;
  final String title;
  final int dayNumber;
  final int displayOrder;
  final double estimatedCostNpr;
  final bool isBooked;
}
