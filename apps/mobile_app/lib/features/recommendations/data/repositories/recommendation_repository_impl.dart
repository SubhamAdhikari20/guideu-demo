import 'package:dio/dio.dart';

import '../../../../core/error/api_error_mapper.dart';
import '../../../../core/error/failures.dart';
import '../../../guides/domain/entities/guide.dart';
import '../../domain/entities/recommended_route.dart';
import '../../domain/repositories/recommendation_repository.dart';
import '../datasources/recommendation_remote_datasource.dart';

class RecommendationRepositoryImpl implements RecommendationRepository {
  const RecommendationRepositoryImpl(this._remote);

  final RecommendationRemoteDataSource _remote;

  @override
  Future<(Failure?, List<RecommendedRoute>?)> getRecommendedRoutes() async {
    try {
      final rows = await _remote.getRecommendedRoutes();
      final items = rows
          .map((r) => RecommendedRoute(
                destination: r.route.toEntity(),
                why: r.why,
                score: r.score,
              ))
          .toList();
      return (null, items);
    } on DioException catch (e) {
      return (mapDioError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  @override
  Future<(Failure?, List<Guide>?)> getRecommendedGuides() async {
    try {
      final models = await _remote.getRecommendedGuides();
      return (null, models.map((m) => m.toEntity()).toList());
    } on DioException catch (e) {
      return (mapDioError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

}
