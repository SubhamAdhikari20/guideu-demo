import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../../core/api/api_endpoints.dart';
import '../../../auth/presentation/providers/auth_providers.dart';

final paymentHistoryProvider =
    FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
      final response = await ref
          .watch(apiClientProvider)
          .dio
          .get(ApiEndpoints.payments);
      final data = response.data;
      final rows = data is Map
          ? data['results'] as List? ?? const []
          : data as List? ?? const [];
      return rows
          .cast<Map>()
          .map((row) => Map<String, dynamic>.from(row))
          .toList();
    });

class PaymentHistoryPage extends ConsumerWidget {
  const PaymentHistoryPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final payments = ref.watch(paymentHistoryProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Payments and receipts')),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(paymentHistoryProvider.future),
        child: payments.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (_, _) => ListView(
            children: [
              const SizedBox(height: 120),
              const Center(child: Text('Could not load payment history.')),
              Center(
                child: TextButton(
                  onPressed: () => ref.invalidate(paymentHistoryProvider),
                  child: const Text('Try again'),
                ),
              ),
            ],
          ),
          data: (items) => items.isEmpty
              ? ListView(
                  children: const [
                    SizedBox(height: 120),
                    Icon(
                      Icons.receipt_long_outlined,
                      size: 52,
                      color: AppColors.textSecondary,
                    ),
                    SizedBox(height: 12),
                    Center(child: Text('No payments yet.')),
                  ],
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: items.length,
                  itemBuilder: (context, index) =>
                      _PaymentCard(payment: items[index]),
                ),
        ),
      ),
    );
  }
}

class _PaymentCard extends ConsumerWidget {
  const _PaymentCard({required this.payment});

  final Map<String, dynamic> payment;

  bool get _hasReceipt => const {
    'SUCCESS',
    'REFUND_PENDING',
    'REFUNDED',
  }.contains(payment['status']);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final created = DateTime.tryParse(
      payment['created_at'] as String? ?? '',
    )?.toLocal();
    final gateway = payment['gateway'] == 'KHALTI' ? 'Khalti' : 'eSewa';
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: AppColors.primary.withValues(alpha: .12),
                  child: const Icon(
                    Icons.account_balance_wallet_outlined,
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '$gateway payment',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      if (created != null)
                        Text(
                          DateFormat('MMM d, yyyy • h:mm a').format(created),
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.textSecondary,
                          ),
                        ),
                    ],
                  ),
                ),
                _StatusChip(status: payment['status'] as String? ?? ''),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              '${payment['currency'] ?? 'NPR'} ${payment['amount'] ?? '0.00'}',
              style: const TextStyle(fontSize: 19, fontWeight: FontWeight.bold),
            ),
            Text(
              payment['gateway_reference'] as String? ?? 'Reference pending',
              style: const TextStyle(
                fontSize: 12,
                color: AppColors.textSecondary,
              ),
            ),
            if (_hasReceipt) ...[
              const SizedBox(height: 10),
              Align(
                alignment: Alignment.centerRight,
                child: OutlinedButton.icon(
                  onPressed: () => _openReceipt(context, ref),
                  icon: const Icon(Icons.receipt_long_outlined),
                  label: const Text('View receipt'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _openReceipt(BuildContext context, WidgetRef ref) async {
    try {
      final response = await ref
          .read(apiClientProvider)
          .dio
          .get('${ApiEndpoints.payments}${payment['id']}/receipt/');
      if (!context.mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => PaymentReceiptPage(
            receipt: Map<String, dynamic>.from(response.data as Map),
          ),
        ),
      );
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not load this receipt.')),
        );
      }
    }
  }
}

class PaymentReceiptPage extends StatelessWidget {
  const PaymentReceiptPage({required this.receipt, super.key});

  final Map<String, dynamic> receipt;

  @override
  Widget build(BuildContext context) {
    final customer = Map<String, dynamic>.from(receipt['customer'] as Map);
    final item = Map<String, dynamic>.from(receipt['item'] as Map);
    final paidAt = DateTime.tryParse(
      receipt['paid_at'] as String? ?? '',
    )?.toLocal();
    final number = receipt['receipt_number'] as String? ?? '';
    return Scaffold(
      appBar: AppBar(
        title: const Text('Payment receipt'),
        actions: [
          IconButton(
            tooltip: 'Copy receipt number',
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: number));
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Receipt number copied.')),
                );
              }
            },
            icon: const Icon(Icons.copy_outlined),
          ),
        ],
      ),
      body: SelectionArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const Icon(Icons.check_circle, size: 58, color: AppColors.primary),
            const SizedBox(height: 10),
            const Center(
              child: Text(
                'Payment received',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(height: 4),
            Center(
              child: Text(
                number,
                style: const TextStyle(color: AppColors.textSecondary),
              ),
            ),
            const SizedBox(height: 24),
            _ReceiptRow(
              label: 'Service',
              value: '${item['type']}: ${item['title']}',
            ),
            _ReceiptRow(
              label: 'Booking reference',
              value: item['reference']?.toString() ?? '',
            ),
            _ReceiptRow(
              label: 'Customer',
              value: customer['name']?.toString() ?? '',
            ),
            _ReceiptRow(
              label: 'Email',
              value: customer['email']?.toString() ?? '',
            ),
            _ReceiptRow(
              label: 'Gateway',
              value: receipt['gateway']?.toString() ?? '',
            ),
            _ReceiptRow(
              label: 'Gateway reference',
              value: receipt['gateway_reference']?.toString() ?? '',
            ),
            if (paidAt != null)
              _ReceiptRow(
                label: 'Paid on',
                value: DateFormat('MMM d, yyyy • h:mm a').format(paidAt),
              ),
            const Divider(height: 30),
            _ReceiptRow(
              label: 'Total',
              value: '${receipt['currency']} ${receipt['amount']}',
              important: true,
            ),
            const SizedBox(height: 18),
            const Text(
              'This receipt was generated by the GuideU server from a verified payment record.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}

class _ReceiptRow extends StatelessWidget {
  const _ReceiptRow({
    required this.label,
    required this.value,
    this.important = false,
  });
  final String label;
  final String value;
  final bool important;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 135,
          child: Text(
            label,
            style: const TextStyle(color: AppColors.textSecondary),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              fontWeight: important ? FontWeight.bold : FontWeight.w500,
              fontSize: important ? 18 : null,
            ),
          ),
        ),
      ],
    ),
  );
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});
  final String status;

  @override
  Widget build(BuildContext context) {
    final success = status == 'SUCCESS';
    return Chip(
      label: Text(
        status.replaceAll('_', ' '),
        style: const TextStyle(fontSize: 10),
      ),
      backgroundColor: success
          ? AppColors.primary.withValues(alpha: .12)
          : null,
      visualDensity: VisualDensity.compact,
    );
  }
}
