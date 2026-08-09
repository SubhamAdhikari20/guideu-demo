import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../../core/error/failures.dart';
import '../../../chat/presentation/pages/chat_room_page.dart';
import '../../../payments/presentation/widgets/payment_sheet.dart';
import '../../domain/entities/booking.dart';
import '../providers/booking_providers.dart';
import '../widgets/booking_card.dart';

/// The logged-in user's bookings, with cancel.
class MyBookingsPage extends ConsumerWidget {
  const MyBookingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bookings = ref.watch(myBookingsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('My Bookings')),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(myBookingsProvider.future),
        child: bookings.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => _ErrorState(
            message: error is Failure ? error.message : 'Something went wrong.',
            onRetry: () => ref.invalidate(myBookingsProvider),
          ),
          data: (items) {
            if (items.isEmpty) {
              return ListView(
                children: const [
                  SizedBox(height: 120),
                  Center(
                    child: Text(
                      'You have no bookings yet.',
                      style: TextStyle(color: AppColors.textSecondary),
                    ),
                  ),
                ],
              );
            }
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
              children: [
                for (final b in items)
                  BookingCard(
                    booking: b,
                    onPay: b.isPending ? () => _pay(context, ref, b) : null,
                    onCancel: b.canCancel
                        ? () => _confirmCancel(context, ref, b)
                        : null,
                    onMessage: () => _openChat(context, b),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }

  void _openChat(BuildContext context, Booking booking) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ChatRoomPage(
          room: 'booking:${booking.id}',
          title: booking.tourPackageTitle,
        ),
      ),
    );
  }

  Future<void> _pay(BuildContext context, WidgetRef ref, Booking booking) async {
    final paid = await showPaymentSheet(
      context,
      bookingId: booking.id,
      amount: booking.totalPrice,
      title: booking.tourPackageTitle,
    );
    if (paid == true && context.mounted) {
      ref.invalidate(myBookingsProvider);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Payment successful. Booking confirmed!')),
      );
    }
  }

  Future<void> _confirmCancel(
    BuildContext context,
    WidgetRef ref,
    Booking booking,
  ) async {
    final yes = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancel booking?'),
        content: Text('Cancel "${booking.tourPackageTitle}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Keep'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text(
              'Cancel booking',
              style: TextStyle(color: AppColors.error),
            ),
          ),
        ],
      ),
    );
    if (yes != true) return;

    final (failure, _) =
        await ref.read(cancelBookingUseCaseProvider).call(booking.id);
    if (!context.mounted) return;
    if (failure == null) {
      ref.invalidate(myBookingsProvider);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(failure.message)),
      );
    }
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        const SizedBox(height: 100),
        Center(
          child: Column(
            children: [
              const Icon(Icons.cloud_off, size: 40, color: AppColors.textSecondary),
              const SizedBox(height: 12),
              Text(message, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              OutlinedButton(onPressed: onRetry, child: const Text('Retry')),
            ],
          ),
        ),
      ],
    );
  }
}
