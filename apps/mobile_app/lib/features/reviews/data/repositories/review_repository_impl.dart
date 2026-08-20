import 'package:dio/dio.dart';

import '../../../../core/error/api_error_mapper.dart';
import '../../../../core/error/failures.dart';
import '../../domain/entities/review.dart';
import '../../domain/repositories/review_repository.dart';
import '../datasources/review_remote_datasource.dart';

class ReviewRepositoryImpl implements ReviewRepository {
  const ReviewRepositoryImpl(this._remote);

  final ReviewRemoteDataSource _remote;

  @override
  Future<(Failure?, List<Review>?)> getGuideReviews(int guideId) async {
    try {
      final models = await _remote.getGuideReviews(guideId);
      return (null, models.map((m) => m.toEntity()).toList());
    } on DioException catch (e) {
      return (mapDioError(e, fallback: 'Could not load reviews.'), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  @override
  Future<(Failure?, ReviewSummary?)> getGuideSummary(int guideId) async {
    try {
      final summary = await _remote.getGuideSummary(guideId);
      return (null, summary);
    } on DioException catch (e) {
      return (mapDioError(e, fallback: 'Could not load the rating.'), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  @override
  Future<(Failure?, Review?)> submitGuideReview({
    required int guideId,
    required int rating,
    required String title,
    required String comment,
  }) async {
    try {
      final model = await _remote.submitGuideReview(
        guideId: guideId,
        rating: rating,
        title: title,
        comment: comment,
      );
      return (null, model.toEntity());
    } on DioException catch (e) {
      return (mapDioError(e, fallback: 'Could not submit your review.'), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

}
