import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/theme/app_colors.dart';
import '../../domain/entities/payment.dart';
import '../../domain/usecases/pay_for_booking_usecase.dart';
import '../providers/payment_providers.dart';
import '../pages/local_sandbox_checkout_page.dart';
import '../pages/sandbox_checkout_page.dart';

/// Opens the payment sheet for a booking. Returns `true` when payment succeeds.
Future<bool?> showPaymentSheet(
  BuildContext context, {
  required int bookingId,
  required double amount,
  required String title,
}) {
  return showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.surface,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (context) =>
        _PaymentSheet(bookingId: bookingId, amount: amount, title: title),
  );
}

class _PaymentSheet extends ConsumerStatefulWidget {
  const _PaymentSheet({
    required this.bookingId,
    required this.amount,
    required this.title,
  });

  final int bookingId;
  final double amount;
  final String title;

  @override
  ConsumerState<_PaymentSheet> createState() => _PaymentSheetState();
}

class _PaymentSheetState extends ConsumerState<_PaymentSheet> {
  PaymentGateway _gateway = PaymentGateway.esewa;
  bool _processing = false;

  Future<void> _pay() async {
    setState(() => _processing = true);
    final (failure, payment) = await ref
        .read(payForBookingUseCaseProvider)
        .call(
          PayForBookingParams(
            bookingId: widget.bookingId,
            amount: widget.amount,
            gateway: _gateway,
          ),
        );
    if (!mounted) return;
    setState(() => _processing = false);
    if (payment != null) {
      final isLocalDemo = payment.mode == 'demo';
      if (!isLocalDemo && !payment.requiresProviderCheckout) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'The payment provider did not return a checkout page.',
            ),
          ),
        );
        return;
      }
      final returned = await Navigator.of(context).push<bool>(
        MaterialPageRoute(
          builder: (_) => isLocalDemo
              ? LocalSandboxCheckoutPage(payment: payment)
              : SandboxCheckoutPage(payment: payment),
        ),
      );
      if (!mounted || returned != true) return;
      final (verifyFailure, verified) = isLocalDemo
          ? await ref.read(paymentRepositoryProvider).confirm(payment.id)
          : await ref.read(paymentRepositoryProvider).verify(payment.id);
      if (!mounted) return;
      if (verified?.isSuccess == true) {
        Navigator.of(context).pop(true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              verifyFailure?.message ?? 'Payment is still pending.',
            ),
          ),
        );
      }
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(failure?.message ?? 'Payment failed.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text(
                'Payment',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.of(context).pop(false),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            widget.title,
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 2),
          Text(
            'Amount: Rs. ${widget.amount.toStringAsFixed(0)}',
            style: const TextStyle(color: AppColors.textSecondary),
          ),
          const SizedBox(height: 16),
          const Text(
            'Choose a payment method',
            style: TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          for (final g in PaymentGateway.values)
            _GatewayTile(
              gateway: g,
              selected: _gateway == g,
              onTap: () => setState(() => _gateway = g),
            ),
          const SizedBox(height: 8),
          Text(
            'Demo mode confirms locally. Sandbox mode opens the official provider checkout and verifies the result on the server.',
            style: TextStyle(
              color: AppColors.textSecondary.withValues(alpha: 0.9),
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _processing ? null : _pay,
              child: _processing
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(
                      'Pay Rs. ${widget.amount.toStringAsFixed(0)} with ${_gateway.label}',
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

class _GatewayTile extends StatelessWidget {
  const _GatewayTile({
    required this.gateway,
    required this.selected,
    required this.onTap,
  });

  final PaymentGateway gateway;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: selected
              ? AppColors.primary.withValues(alpha: 0.08)
              : AppColors.inputFill,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: selected ? AppColors.primary : AppColors.border,
            width: selected ? 1.5 : 1,
          ),
        ),
        child: Row(
          children: [
            Icon(
              Icons.account_balance_wallet_outlined,
              color: selected ? AppColors.primary : AppColors.textSecondary,
            ),
            const SizedBox(width: 12),
            Text(
              gateway.label,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            const Spacer(),
            if (selected)
              const Icon(
                Icons.check_circle,
                color: AppColors.primary,
                size: 20,
              ),
          ],
        ),
      ),
    );
  }
}
