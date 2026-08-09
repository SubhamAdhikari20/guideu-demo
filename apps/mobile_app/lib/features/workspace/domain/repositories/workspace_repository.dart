import '../../../../core/error/failures.dart';
import '../entities/trip.dart';

abstract interface class WorkspaceRepository {
  Future<(Failure?, List<TravelTrip>?)> getTrips();
  Future<(Failure?, TravelTrip?)> getTrip(int id);
  Future<(Failure?, TravelTrip?)> createTrip({
    required String title,
    required DateTime startDate,
    required DateTime endDate,
    required double budgetNpr,
  });
  Future<(Failure?, bool?)> deleteTrip(int id);
  Future<(Failure?, bool?)> addItem({
    required int tripId,
    required String itemType,
    required String title,
    required int dayNumber,
    required double costNpr,
  });
  Future<(Failure?, bool?)> deleteItem(int itemId);
  Future<(Failure?, bool?)> reorder(List<TripItem> ordered);
  Future<(Failure?, TravelTrip?)> applyAiSuggestions(int tripId);
}
