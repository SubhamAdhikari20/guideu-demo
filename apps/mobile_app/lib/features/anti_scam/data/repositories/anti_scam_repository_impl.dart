import 'package:dio/dio.dart';

import '../../../../core/error/api_error_mapper.dart';
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
      return (mapDioError(e), null);
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
      return (mapDioError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  @override
  Future<(Failure?, List<String>?)> getRegionNames() async {
    try {
      return (null, await _remote.getRegionNames());
    } on DioException catch (e) {
      return (mapDioError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

}
