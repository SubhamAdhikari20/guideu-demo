import 'package:dio/dio.dart';

import '../../../../core/error/failures.dart';
import '../../domain/entities/festival.dart';
import '../../domain/repositories/festival_repository.dart';
import '../datasources/festival_remote_datasource.dart';

class FestivalRepositoryImpl implements FestivalRepository {
  const FestivalRepositoryImpl(this._remote);

  final FestivalRemoteDataSource _remote;

  @override
  Future<(Failure?, List<FestivalMonth>?)> getUpcoming({int months = 12}) async {
    try {
      return (null, await _remote.getUpcoming(months: months));
    } on DioException catch (e) {
      if (e.type == DioExceptionType.connectionError ||
          e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.receiveTimeout) {
        return (const NetworkFailure(), null);
      }
      return (ServerFailure('Could not load festivals.', statusCode: e.response?.statusCode), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }
}
