import 'package:dio/dio.dart';

import '../../../../core/error/api_error_mapper.dart';
import '../../../../core/error/failures.dart';
import '../../domain/entities/payment.dart';
import '../../domain/repositories/payment_repository.dart';
import '../datasources/payment_remote_datasource.dart';

class PaymentRepositoryImpl implements PaymentRepository {
  const PaymentRepositoryImpl(this._remote);

  final PaymentRemoteDataSource _remote;

  @override
  Future<(Failure?, Payment?)> initiate({
    required int bookingId,
    required double amount,
    required PaymentGateway gateway,
  }) async {
    try {
      final model = await _remote.initiate(
        bookingId: bookingId,
        amount: amount,
        gateway: gateway,
      );
      return (null, model.toEntity());
    } on DioException catch (e) {
      return (mapDioError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  @override
  Future<(Failure?, Payment?)> confirm(int paymentId) async {
    try {
      final model = await _remote.confirm(paymentId);
      return (null, model.toEntity());
    } on DioException catch (e) {
      return (mapDioError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  @override
  Future<(Failure?, Payment?)> verify(int paymentId) async {
    try {
      final model = await _remote.verify(paymentId);
      return (null, model.toEntity());
    } on DioException catch (e) {
      return (mapDioError(e, fallback: 'The payment provider has not verified this payment yet.'), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

}
