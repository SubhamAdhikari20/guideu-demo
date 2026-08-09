import 'package:dio/dio.dart';

import '../../../../core/error/failures.dart';
import '../../../destinations/domain/entities/destination.dart';
import '../../../guides/domain/entities/guide.dart';
import '../../domain/repositories/recommendation_repository.dart';
import '../datasources/recommendation_remote_datasource.dart';

class RecommendationRepositoryImpl implements RecommendationRepository {
  const RecommendationRepositoryImpl(this._remote);

  final RecommendationRemoteDataSource _remote;

  @override
  Future<(Failure?, List<Destination>?)> getRecommendedRoutes() async {
    try {
      final models = await _remote.getRecommendedRoutes();
      return (null, models.map((m) => m.toEntity()).toList());
    } on DioException catch (e) {
      return (_mapError(e), null);
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
      return (_mapError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  Failure _mapError(DioException e) {
    if (e.type == DioExceptionType.connectionError ||
        e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout) {
      return const NetworkFailure();
    }
    return ServerFailure(
      'Could not load recommendations.',
      statusCode: e.response?.statusCode,
    );
  }
}
