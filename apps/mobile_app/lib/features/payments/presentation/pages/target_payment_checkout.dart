import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../../core/error/api_error_mapper.dart';
import '../../../auth/presentation/providers/auth_providers.dart';
import '../../data/models/payment_model.dart';
import '../../domain/entities/payment.dart';
import 'local_sandbox_checkout_page.dart';
import 'sandbox_checkout_page.dart';

/// Checkout helper for guide requests and hotel/flight/bus reservations.
/// The target id is sent to the server; amount is intentionally never accepted.
Future<bool> startTargetPayment(
  BuildContext context,
  WidgetRef ref, {
  required Map<String, dynamic> target,
  String? gateway,
}) async {
  final selectedGateway = gateway ?? await _chooseGateway(context);
  if (selectedGateway == null || !context.mounted) return false;
  try {
    final response = await ref
        .read(apiClientProvider)
        .dio
        .post(
          ApiEndpoints.payments,
          data: {...target, 'gateway': selectedGateway},
        );
    final payment = PaymentModel.fromJson(
      Map<String, dynamic>.from(response.data as Map),
    ).toEntity();
    if (!context.mounted) return false;
    if (payment.mode == 'demo') {
      final accepted = await Navigator.of(context).push<bool>(
        MaterialPageRoute(
          builder: (_) => LocalSandboxCheckoutPage(payment: payment),
        ),
      );
      if (accepted != true) return false;
      final confirmed = await ref
          .read(apiClientProvider)
          .dio
          .post('${ApiEndpoints.payments}${payment.id}/confirm/');
      return (confirmed.data as Map)['status'] == 'SUCCESS';
    }
    if (!payment.requiresProviderCheckout || !context.mounted) return false;
    final returned = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => SandboxCheckoutPage(payment: payment)),
    );
    if (returned != true) return false;
    final verification = await ref
        .read(apiClientProvider)
        .dio
        .post('${ApiEndpoints.payments}${payment.id}/verify/');
    return (verification.data as Map)['status'] == 'SUCCESS';
  } on DioException catch (error) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            mapDioError(error, fallback: 'Could not start payment.').message,
          ),
        ),
      );
    }
    return false;
  } catch (_) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Could not start payment. Please try again.'),
        ),
      );
    }
    return false;
  }
}

Future<String?> _chooseGateway(BuildContext context) {
  return showModalBottomSheet<String>(
    context: context,
    showDragHandle: true,
    builder: (sheetContext) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Choose a payment gateway',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            for (final gateway in PaymentGateway.values)
              ListTile(
                leading: const Icon(Icons.account_balance_wallet_outlined),
                title: Text(gateway.label),
                subtitle: const Text('Local sandbox or provider test checkout'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(sheetContext).pop(gateway.api),
              ),
          ],
        ),
      ),
    ),
  );
}
