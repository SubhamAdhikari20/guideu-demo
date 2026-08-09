import '../../../../core/error/failures.dart';
import '../../../destinations/domain/entities/destination.dart';
import '../../../guides/domain/entities/guide.dart';

/// Personalised recommendations for the signed-in tourist.
abstract interface class RecommendationRepository {
  Future<(Failure?, List<Destination>?)> getRecommendedRoutes();

  Future<(Failure?, List<Guide>?)> getRecommendedGuides();
}
