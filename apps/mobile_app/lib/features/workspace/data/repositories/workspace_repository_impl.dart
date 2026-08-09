import 'package:dio/dio.dart';

import '../../../../core/error/failures.dart';
import '../../domain/entities/trip.dart';
import '../../domain/repositories/workspace_repository.dart';
import '../datasources/workspace_remote_datasource.dart';

class WorkspaceRepositoryImpl implements WorkspaceRepository {
  const WorkspaceRepositoryImpl(this._remote);

  final WorkspaceRemoteDataSource _remote;

  @override
  Future<(Failure?, List<TravelTrip>?)> getTrips() => _guard(() => _remote.getTrips());

  @override
  Future<(Failure?, TravelTrip?)> getTrip(int id) => _guard(() => _remote.getTrip(id));

  @override
  Future<(Failure?, TravelTrip?)> createTrip({
    required String title,
    required DateTime startDate,
    required DateTime endDate,
    required double budgetNpr,
  }) =>
      _guard(() => _remote.createTrip(
            title: title, startDate: startDate, endDate: endDate, budgetNpr: budgetNpr,
          ));

  @override
  Future<(Failure?, bool?)> deleteTrip(int id) =>
      _guard(() async { await _remote.deleteTrip(id); return true; });

  @override
  Future<(Failure?, bool?)> addItem({
    required int tripId,
    required String itemType,
    required String title,
    required int dayNumber,
    required double costNpr,
  }) =>
      _guard(() async {
        await _remote.addItem(
          tripId: tripId, itemType: itemType, title: title, dayNumber: dayNumber, costNpr: costNpr,
        );
        return true;
      });

  @override
  Future<(Failure?, bool?)> deleteItem(int itemId) =>
      _guard(() async { await _remote.deleteItem(itemId); return true; });

  @override
  Future<(Failure?, bool?)> reorder(List<TripItem> ordered) =>
      _guard(() async { await _remote.reorder(ordered); return true; });

  @override
  Future<(Failure?, TravelTrip?)> applyAiSuggestions(int tripId) =>
      _guard(() => _remote.applyAiSuggestions(tripId));

  /// Shared try/catch that maps Dio/other errors to a [Failure].
  Future<(Failure?, T?)> _guard<T>(Future<T> Function() run) async {
    try {
      return (null, await run());
    } on DioException catch (e) {
      if (e.type == DioExceptionType.connectionError ||
          e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.receiveTimeout) {
        return (const NetworkFailure(), null);
      }
      final data = e.response?.data;
      var message = 'Something went wrong. Please try again.';
      if (data is Map && data['detail'] is String) message = data['detail'] as String;
      return (ServerFailure(message, statusCode: e.response?.statusCode), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }
}
