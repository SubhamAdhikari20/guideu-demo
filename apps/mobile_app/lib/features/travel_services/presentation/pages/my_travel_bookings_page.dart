import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../../core/api/api_endpoints.dart';
import '../../../auth/presentation/providers/auth_providers.dart';
import '../../../payments/presentation/pages/target_payment_checkout.dart';

final travelBookingsProvider = FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final response = await ref.watch(apiClientProvider).dio.get(ApiEndpoints.travelServiceBookings);
  final data = response.data;
  final rows = data is Map ? data['results'] as List? ?? const [] : data as List? ?? const [];
  return rows.cast<Map>().map((row) => Map<String, dynamic>.from(row)).toList();
});

class MyTravelBookingsPage extends ConsumerWidget {
  const MyTravelBookingsPage({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bookings = ref.watch(travelBookingsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Travel bookings')),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(travelBookingsProvider.future),
        child: bookings.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (_, _) => ListView(children: const [SizedBox(height: 100), Center(child: Text('Could not load bookings.'))]),
          data: (items) => items.isEmpty
              ? ListView(children: const [SizedBox(height: 100), Center(child: Text('No hotel, flight, or bus bookings yet.'))])
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: items.length,
                  itemBuilder: (context, index) {
                    final booking = items[index];
                    final offering = Map<String, dynamic>.from(booking['offering_details'] as Map);
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Row(children: [Expanded(child: Text(offering['title'] as String? ?? '', style: const TextStyle(fontWeight: FontWeight.bold))), _StatusChip(status: booking['status'] as String? ?? '')]),
                          Text('${offering['service_type']} • ${booking['reference']}', style: const TextStyle(color: AppColors.textSecondary)),
                          const SizedBox(height: 8),
                          Text('${booking['currency']} ${booking['total_price']}', style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
                          if (booking['start_date'] != null) Text('${DateFormat.yMMMd().format(DateTime.parse(booking['start_date'] as String))} – ${DateFormat.yMMMd().format(DateTime.parse(booking['end_date'] as String))}'),
                          if (booking['status'] == 'PAYMENT_PENDING') ...[
                            const SizedBox(height: 10),
                            Row(children: [
                              Expanded(child: OutlinedButton(onPressed: () => _cancel(ref, booking['id'] as int), child: const Text('Cancel'))),
                              const SizedBox(width: 10),
                              Expanded(child: ElevatedButton(onPressed: () => _pay(context, ref, booking['id'] as int), child: const Text('Pay now'))),
                            ]),
                          ],
                        ]),
                      ),
                    );
                  },
                ),
        ),
      ),
    );
  }

  Future<void> _cancel(WidgetRef ref, int id) async {
    await ref.read(apiClientProvider).dio.post('${ApiEndpoints.travelServiceBookings}$id/cancel/');
    ref.invalidate(travelBookingsProvider);
  }

  Future<void> _pay(BuildContext context, WidgetRef ref, int id) async {
    final paid = await startTargetPayment(context, ref, target: {'service_booking': id}, gateway: 'ESEWA');
    if (!context.mounted) return;
    if (paid) ref.invalidate(travelBookingsProvider);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(paid ? 'Payment verified. Booking confirmed.' : 'Payment was not completed.')));
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});
  final String status;
  @override
  Widget build(BuildContext context) => Chip(label: Text(status.replaceAll('_', ' '), style: const TextStyle(fontSize: 10)), backgroundColor: status == 'CONFIRMED' ? AppColors.primary.withValues(alpha: .12) : null);
}
