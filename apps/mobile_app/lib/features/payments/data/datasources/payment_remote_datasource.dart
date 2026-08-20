import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../domain/entities/payment.dart';
import '../models/payment_model.dart';

/// Talks to the core-engine payments endpoints over Dio.
class PaymentRemoteDataSource {
  const PaymentRemoteDataSource(this._dio);

  final Dio _dio;

  Future<PaymentModel> initiate({
    required int bookingId,
    required double amount,
    required PaymentGateway gateway,
  }) async {
    final resp = await _dio.post(
      ApiEndpoints.payments,
      data: <String, dynamic>{
        'booking': bookingId,
        'amount': amount,
        'currency': 'NPR',
        'gateway': gateway.api,
      },
    );
    return PaymentModel.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<PaymentModel> confirm(int paymentId) async {
    final resp = await _dio.post('${ApiEndpoints.payments}$paymentId/confirm/');
    return PaymentModel.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<PaymentModel> verify(int paymentId) async {
    final resp = await _dio.post('${ApiEndpoints.payments}$paymentId/verify/');
    return PaymentModel.fromJson(resp.data as Map<String, dynamic>);
  }
}
