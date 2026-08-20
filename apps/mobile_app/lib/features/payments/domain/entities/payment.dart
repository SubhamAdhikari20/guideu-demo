/// Supported payment gateways (subset of the backend `PaymentTransaction.Gateway`).
enum PaymentGateway {
  esewa('ESEWA', 'eSewa'),
  khalti('KHALTI', 'Khalti');

  const PaymentGateway(this.api, this.label);

  final String api;
  final String label;
}

/// Pure domain entity for a payment (core-engine `PaymentTransaction`).
class Payment {
  const Payment({
    required this.id,
    required this.bookingId,
    required this.amount,
    required this.currency,
    required this.status,
    required this.gateway,
    required this.mode,
    this.checkoutUrl,
    this.checkoutPayload,
  });

  final int id;
  final int? bookingId;
  final double amount;
  final String currency;
  final String status; // PENDING | SUCCESS | FAILED | REFUNDED
  final String gateway;
  final String mode;
  final String? checkoutUrl;
  final Map<String, dynamic>? checkoutPayload;

  bool get isSuccess => status.toUpperCase() == 'SUCCESS';
  bool get requiresProviderCheckout => mode != 'demo' && !isSuccess && checkoutUrl != null;
}
