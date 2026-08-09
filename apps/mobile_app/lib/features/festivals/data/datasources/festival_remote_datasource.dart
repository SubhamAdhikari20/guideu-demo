import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../domain/entities/festival.dart';

/// Reads the upcoming-festivals calendar from the core-engine info hub.
class FestivalRemoteDataSource {
  const FestivalRemoteDataSource(this._dio);

  final Dio _dio;

  Future<List<FestivalMonth>> getUpcoming({int months = 12}) async {
    final resp = await _dio.get(
      ApiEndpoints.eventsUpcoming,
      queryParameters: <String, dynamic>{'months': months},
    );
    final data = resp.data;
    final monthsJson = (data is Map && data['months'] is List)
        ? data['months'] as List<dynamic>
        : const <dynamic>[];
    return monthsJson.map((m) => _month(m as Map<String, dynamic>)).toList();
  }

  FestivalMonth _month(Map<String, dynamic> json) {
    final festivals = (json['festivals'] as List<dynamic>? ?? const [])
        .map((f) => _festival(f as Map<String, dynamic>))
        .toList();
    return FestivalMonth(
      month: (json['month'] ?? 0) as int,
      monthName: (json['month_name'] ?? '') as String,
      festivals: festivals,
    );
  }

  Festival _festival(Map<String, dynamic> json) {
    return Festival(
      name: (json['festival_name'] ?? '') as String,
      type: (json['event_type'] ?? '') as String,
      significance: (json['significance'] ?? '') as String,
      durationDays: (json['duration_days'] ?? 0) as int,
      badgeEligible: (json['badge_eligible'] ?? false) as bool,
      badgePoints: (json['badge_points'] ?? 0) as int,
      regions: (json['regions'] as List<dynamic>? ?? const [])
          .map((e) => e.toString())
          .toList(),
    );
  }
}
