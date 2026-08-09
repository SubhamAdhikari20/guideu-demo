import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../models/price_check_result_model.dart';

/// Talks to the core-engine `trust` app (anti-scam) and the regions catalog.
class AntiScamRemoteDataSource {
  const AntiScamRemoteDataSource(this._dio);

  final Dio _dio;

  Future<PriceCheckResultModel> checkPrice({
    required String serviceType,
    required int quotedPriceNpr,
    String? region,
    String? season,
  }) async {
    final resp = await _dio.post(
      ApiEndpoints.priceCheck,
      data: <String, dynamic>{
        'service_type': serviceType,
        'quoted_price_npr': quotedPriceNpr,
        if (region != null && region.isNotEmpty) 'region': region,
        if (season != null && season.isNotEmpty) 'season': season,
      },
    );
    return PriceCheckResultModel(resp.data as Map<String, dynamic>);
  }

  Future<void> reportScam({
    required String serviceType,
    required String region,
    required int quotedPriceNpr,
    String? season,
    String description = '',
  }) async {
    await _dio.post(
      ApiEndpoints.scamReports,
      data: <String, dynamic>{
        'service_type': serviceType,
        'region': region,
        'quoted_price_npr': quotedPriceNpr,
        if (season != null && season.isNotEmpty) 'season': season,
        'description': description,
      },
    );
  }

  Future<List<String>> getRegionNames() async {
    final resp = await _dio.get(ApiEndpoints.regions);
    final data = resp.data;
    final list = (data is Map && data['results'] is List)
        ? data['results'] as List<dynamic>
        : (data is List ? data : const <dynamic>[]);
    return list
        .map((e) => (e as Map<String, dynamic>)['name']?.toString() ?? '')
        .where((s) => s.isNotEmpty)
        .toList();
  }
}
