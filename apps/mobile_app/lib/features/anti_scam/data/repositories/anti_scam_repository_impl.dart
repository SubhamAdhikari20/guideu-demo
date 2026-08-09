import 'package:dio/dio.dart';

import '../../../../core/error/failures.dart';
import '../../domain/entities/price_check_result.dart';
import '../../domain/repositories/anti_scam_repository.dart';
import '../datasources/anti_scam_remote_datasource.dart';

class AntiScamRepositoryImpl implements AntiScamRepository {
  const AntiScamRepositoryImpl(this._remote);

  final AntiScamRemoteDataSource _remote;

  @override
  Future<(Failure?, PriceCheckResult?)> checkPrice({
    required String serviceType,
    required int quotedPriceNpr,
    String? region,
    String? season,
  }) async {
    try {
      final model = await _remote.checkPrice(
        serviceType: serviceType,
        quotedPriceNpr: quotedPriceNpr,
        region: region,
        season: season,
      );
      return (null, model.toEntity());
    } on DioException catch (e) {
      return (_mapError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  @override
  Future<(Failure?, bool?)> reportScam({
    required String serviceType,
    required String region,
    required int quotedPriceNpr,
    String? season,
    String description = '',
  }) async {
    try {
      await _remote.reportScam(
        serviceType: serviceType,
        region: region,
        quotedPriceNpr: quotedPriceNpr,
        season: season,
        description: description,
      );
      return (null, true);
    } on DioException catch (e) {
      return (_mapError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  @override
  Future<(Failure?, List<String>?)> getRegionNames() async {
    try {
      return (null, await _remote.getRegionNames());
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
    final data = e.response?.data;
    var message = 'Could not complete the request. Please try again.';
    if (data is Map && data['detail'] is String) {
      message = data['detail'] as String;
    }
    return ServerFailure(message, statusCode: e.response?.statusCode);
  }
}
