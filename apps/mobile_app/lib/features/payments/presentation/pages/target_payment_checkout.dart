import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../auth/presentation/providers/auth_providers.dart';
import '../../data/models/payment_model.dart';
import 'sandbox_checkout_page.dart';

/// Checkout helper for guide requests and hotel/flight/bus reservations.
/// The target id is sent to the server; amount is intentionally never accepted.
Future<bool> startTargetPayment(
  BuildContext context,
  WidgetRef ref, {
  required Map<String, dynamic> target,
  String gateway = 'KHALTI',
}) async {
  try {
    final response = await ref.read(apiClientProvider).dio.post(
      ApiEndpoints.payments,
      data: {...target, 'gateway': gateway},
    );
    final payment = PaymentModel.fromJson(Map<String, dynamic>.from(response.data as Map)).toEntity();
    if (payment.mode == 'demo') {
      await ref.read(apiClientProvider).dio.post('${ApiEndpoints.payments}${payment.id}/confirm/');
      return true;
    }
    if (!payment.requiresProviderCheckout || !context.mounted) return false;
    final returned = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => SandboxCheckoutPage(payment: payment)),
    );
    if (returned != true) return false;
    final verification = await ref.read(apiClientProvider).dio.post(
      '${ApiEndpoints.payments}${payment.id}/verify/',
    );
    return (verification.data as Map)['status'] == 'SUCCESS';
  } catch (_) {
    return false;
  }
}
