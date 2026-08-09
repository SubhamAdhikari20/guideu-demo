import '../../domain/entities/trip.dart';

/// Maps the core-engine workspace JSON to [TravelTrip] / [TripItem] entities.
class TripModel {
  static TravelTrip fromJson(Map<String, dynamic> json) {
    final itemsJson = json['items'];
    return TravelTrip(
      id: json['id'] as int,
      title: (json['title'] ?? '') as String,
      startDate: DateTime.tryParse((json['start_date'] ?? '') as String) ?? DateTime.now(),
      endDate: DateTime.tryParse((json['end_date'] ?? '') as String) ?? DateTime.now(),
      totalBudgetNpr: _toDouble(json['total_budget_npr']),
      currencyPreference: (json['currency_preference'] ?? 'NPR') as String,
      itemCount: (json['item_count'] ?? 0) as int,
      totalPlannedCostNpr: _toDouble(json['total_planned_cost_npr']),
      tripDays: (json['trip_days'] ?? 1) as int,
      notes: (json['notes'] ?? '') as String,
      items: itemsJson is List
          ? itemsJson.map((e) => itemFromJson(e as Map<String, dynamic>)).toList()
          : const [],
    );
  }

  static TripItem itemFromJson(Map<String, dynamic> json) {
    return TripItem(
      id: json['id'] as int,
      itemType: (json['item_type'] ?? 'custom') as String,
      title: (json['title'] ?? '') as String,
      dayNumber: (json['day_number'] ?? 1) as int,
      displayOrder: (json['display_order'] ?? 0) as int,
      estimatedCostNpr: _toDouble(json['estimated_cost_npr']),
      isBooked: (json['is_booked'] ?? false) as bool,
    );
  }

  static double _toDouble(dynamic v) {
    if (v is num) return v.toDouble();
    if (v is String) return double.tryParse(v) ?? 0;
    return 0;
  }
}
