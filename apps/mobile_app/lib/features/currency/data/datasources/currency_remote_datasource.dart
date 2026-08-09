import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';

/// Reads NPR-based exchange rates from the core-engine.
class CurrencyRemoteDataSource {
  const CurrencyRemoteDataSource(this._dio);

  final Dio _dio;

  Future<Map<String, double>> getRates() async {
    final resp = await _dio.get(ApiEndpoints.currencyRates);
    final data = resp.data;
    final rates = (data is Map && data['rates'] is Map)
        ? data['rates'] as Map
        : const {};
    return rates.map((k, v) => MapEntry(k.toString(), (v as num).toDouble()));
  }
}
