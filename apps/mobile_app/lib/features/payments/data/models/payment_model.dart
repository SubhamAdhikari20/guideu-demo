import '../../domain/entities/payment.dart';

/// Maps the core-engine `PaymentTransaction` JSON to a [Payment] entity.
class PaymentModel {
  const PaymentModel({
    required this.id,
    required this.booking,
    required this.amount,
    required this.currency,
    required this.status,
    required this.gateway,
    required this.mode,
    this.checkoutUrl,
    this.checkoutPayload,
  });

  final int id;
  final int? booking;
  final double amount;
  final String currency;
  final String status;
  final String gateway;
  final String mode;
  final String? checkoutUrl;
  final Map<String, dynamic>? checkoutPayload;

  factory PaymentModel.fromJson(Map<String, dynamic> json) {
    return PaymentModel(
      id: json['id'] as int,
      booking: json['booking'] as int?,
      amount: _toDouble(json['amount']),
      currency: (json['currency'] ?? 'NPR') as String,
      status: (json['status'] ?? 'PENDING') as String,
      gateway: (json['gateway'] ?? 'OTHER') as String,
      mode: (json['mode'] ?? 'demo') as String,
      checkoutUrl: json['checkout_url'] as String?,
      checkoutPayload: json['checkout_payload'] is Map
          ? Map<String, dynamic>.from(json['checkout_payload'] as Map)
          : null,
    );
  }

  static double _toDouble(dynamic value) {
    if (value is num) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? 0;
    return 0;
  }

  Payment toEntity() => Payment(
        id: id,
        bookingId: booking,
        amount: amount,
        currency: currency,
        status: status,
        gateway: gateway,
        mode: mode,
        checkoutUrl: checkoutUrl,
        checkoutPayload: checkoutPayload,
      );
}
