import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../models/trip_model.dart';
import '../../domain/entities/trip.dart';

/// Talks to the core-engine travel workspace endpoints.
class WorkspaceRemoteDataSource {
  const WorkspaceRemoteDataSource(this._dio);

  final Dio _dio;

  Future<List<TravelTrip>> getTrips() async {
    final resp = await _dio.get(ApiEndpoints.workspaceTrips);
    return _results(resp.data)
        .map((e) => TripModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<TravelTrip> getTrip(int id) async {
    final resp = await _dio.get('${ApiEndpoints.workspaceTrips}$id/');
    return TripModel.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<TravelTrip> createTrip({
    required String title,
    required DateTime startDate,
    required DateTime endDate,
    required double budgetNpr,
  }) async {
    final resp = await _dio.post(
      ApiEndpoints.workspaceTrips,
      data: <String, dynamic>{
        'title': title,
        'start_date': _d(startDate),
        'end_date': _d(endDate),
        'total_budget_npr': budgetNpr,
      },
    );
    return TripModel.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<void> deleteTrip(int id) => _dio.delete('${ApiEndpoints.workspaceTrips}$id/');

  Future<void> addItem({
    required int tripId,
    required String itemType,
    required String title,
    required int dayNumber,
    required double costNpr,
  }) async {
    await _dio.post(
      ApiEndpoints.workspaceItems,
      data: <String, dynamic>{
        'workspace': tripId,
        'item_type': itemType,
        'custom_title': title,
        'day_number': dayNumber,
        'estimated_cost_npr': costNpr,
      },
    );
  }

  Future<void> deleteItem(int itemId) =>
      _dio.delete('${ApiEndpoints.workspaceItems}$itemId/');

  Future<void> reorder(List<TripItem> ordered) async {
    final payload = <Map<String, dynamic>>[];
    for (var i = 0; i < ordered.length; i++) {
      payload.add({
        'item_id': ordered[i].id,
        'day_number': ordered[i].dayNumber,
        'display_order': i,
      });
    }
    await _dio.post(ApiEndpoints.workspaceItemsReorder, data: payload);
  }

  Future<TravelTrip> applyAiSuggestions(int tripId) async {
    final resp = await _dio.post(ApiEndpoints.workspaceApplySuggestions(tripId));
    return TripModel.fromJson(resp.data as Map<String, dynamic>);
  }

  String _d(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  List<dynamic> _results(dynamic data) {
    if (data is Map && data['results'] is List) return data['results'] as List<dynamic>;
    if (data is List) return data;
    return const [];
  }
}
