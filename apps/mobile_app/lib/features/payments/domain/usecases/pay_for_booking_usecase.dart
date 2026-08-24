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

/// Creates a server-priced payment. The presentation layer completes either
/// the safe local sandbox or the provider-hosted sandbox checkout.
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
    return (null, payment);
  }
}
