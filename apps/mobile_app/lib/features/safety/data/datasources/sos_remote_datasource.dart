import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';

/// Raises a safety SOS alert on the core-engine. Location is optional — a future
/// build (or an IoT wearable) can attach GPS coordinates to the same call.
class SosRemoteDataSource {
  const SosRemoteDataSource(this._dio);

  final Dio _dio;

  Future<void> sendSos({String message = '', double? latitude, double? longitude}) async {
    await _dio.post(
      ApiEndpoints.sosAlerts,
      data: <String, dynamic>{
        'message': message,
        'latitude': ?latitude,
        'longitude': ?longitude,
      },
    );
  }
}
