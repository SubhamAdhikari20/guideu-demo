import '../../../../core/error/failures.dart';
import '../../../../core/usecases/usecase.dart';
import '../entities/payment.dart';
import '../repositories/payment_repository.dart';

class PayForBookingParams {
  const PayForBookingParams({
    required this.bookingId,
    required this.amount,
    required this.gateway,
  });

  final int bookingId;
  final double amount;
  final PaymentGateway gateway;
}

/// Creates a server-priced payment. Local demo mode confirms immediately;
/// sandbox/live mode returns the provider checkout for the presentation layer.
class PayForBookingUseCase implements UseCase<Payment, PayForBookingParams> {
  const PayForBookingUseCase(this._repository);

  final PaymentRepository _repository;

  @override
  Future<(Failure?, Payment?)> call(PayForBookingParams params) async {
    final (initFailure, payment) = await _repository.initiate(
      bookingId: params.bookingId,
      amount: params.amount,
      gateway: params.gateway,
    );
    if (initFailure != null || payment == null) {
      return (initFailure, null);
    }
    if (payment.mode == 'demo') return _repository.confirm(payment.id);
    return (null, payment);
  }
}
