import '../../../../core/error/failures.dart';
import '../../../guides/domain/entities/guide.dart';
import '../entities/recommended_route.dart';

/// Personalised recommendations for the signed-in tourist.
abstract interface class RecommendationRepository {
  Future<(Failure?, List<RecommendedRoute>?)> getRecommendedRoutes();

  Future<(Failure?, List<Guide>?)> getRecommendedGuides();
}
