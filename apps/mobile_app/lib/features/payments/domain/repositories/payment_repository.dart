import '../../../../core/error/failures.dart';
import '../entities/payment.dart';

/// Contract for paying for a booking (clean architecture).
abstract interface class PaymentRepository {
  /// Creates a pending payment for a booking via the chosen gateway.
  Future<(Failure?, Payment?)> initiate({
    required int bookingId,
    required double amount,
    required PaymentGateway gateway,
  });

  /// Confirms a payment (stands in for the gateway success callback).
  Future<(Failure?, Payment?)> confirm(int paymentId);
  Future<(Failure?, Payment?)> verify(int paymentId);
}
