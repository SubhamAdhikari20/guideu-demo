import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../../core/api/api_endpoints.dart';
import '../../../auth/presentation/providers/auth_providers.dart';
import '../../../chat/presentation/pages/chat_room_page.dart';
import '../../../payments/presentation/pages/target_payment_checkout.dart';

final guideRequestsProvider = FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final response = await ref.watch(apiClientProvider).dio.get(ApiEndpoints.guideRequests);
  final data = response.data;
  final rows = data is Map ? data['results'] as List? ?? const [] : data as List? ?? const [];
  return rows.cast<Map>().map((row) => Map<String, dynamic>.from(row)).toList();
});

class GuideRequestsPage extends ConsumerWidget {
  const GuideRequestsPage({this.guideMode = false, this.assignmentsOnly = false, super.key});
  final bool guideMode;
  final bool assignmentsOnly;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final requests = ref.watch(guideRequestsProvider);
    return Scaffold(
      appBar: AppBar(title: Text(assignmentsOnly ? 'My assignments' : guideMode ? 'Nearby requests' : 'Guide requests')),
      floatingActionButton: guideMode ? null : FloatingActionButton.extended(
        onPressed: () => _newRequest(context, ref),
        icon: const Icon(Icons.add_location_alt_outlined),
        label: const Text('Request guide'),
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(guideRequestsProvider.future),
        child: requests.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (_, _) => ListView(children: const [SizedBox(height: 110), Center(child: Text('Could not load guide requests.'))]),
          data: (all) {
            final items = assignmentsOnly
                ? all.where((row) => !['SEARCHING', 'OFFERED', 'CANCELLED', 'EXPIRED'].contains(row['status'])).toList()
                : all;
            if (items.isEmpty) return ListView(children: [const SizedBox(height: 110), Center(child: Text(guideMode ? 'No guide requests are available right now.' : 'Start a request and compare offers from verified guides.'))]);
            return ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 90),
              itemCount: items.length,
              itemBuilder: (context, index) => _RequestCard(
                request: items[index],
                guideMode: guideMode,
                onChanged: () => ref.invalidate(guideRequestsProvider),
              ),
            );
          },
        ),
      ),
    );
  }

  Future<void> _newRequest(BuildContext context, WidgetRef ref) async {
    final pickup = TextEditingController(text: 'Thamel, Kathmandu');
    final destination = TextEditingController();
    final requirements = TextEditingController();
    final fare = TextEditingController();
    var duration = 4;
    var group = 1;
    var scheduled = DateTime.now().add(const Duration(hours: 1));
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setState) => Padding(
          padding: EdgeInsets.fromLTRB(20, 16, 20, MediaQuery.viewInsetsOf(context).bottom + 24),
          child: SingleChildScrollView(
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              const Text('Request a guide', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const Text('Set your trip and offer a fair price. Nearby verified guides can respond.', style: TextStyle(color: AppColors.textSecondary)),
              const SizedBox(height: 16),
              TextField(controller: pickup, decoration: const InputDecoration(labelText: 'Pickup', prefixIcon: Icon(Icons.my_location))),
              const SizedBox(height: 12),
              TextField(controller: destination, decoration: const InputDecoration(labelText: 'Destination', prefixIcon: Icon(Icons.location_on_outlined))),
              const SizedBox(height: 12),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.schedule),
                title: const Text('Start time'),
                subtitle: Text(DateFormat('MMM d, h:mm a').format(scheduled)),
                onTap: () async {
                  final day = await showDatePicker(context: context, firstDate: DateTime.now(), lastDate: DateTime.now().add(const Duration(days: 365)), initialDate: scheduled);
                  if (day == null || !context.mounted) return;
                  final time = await showTimePicker(context: context, initialTime: TimeOfDay.fromDateTime(scheduled));
                  if (time != null) setState(() => scheduled = DateTime(day.year, day.month, day.day, time.hour, time.minute));
                },
              ),
              _NumberRow(label: 'Duration (hours)', value: duration, max: 24, onChanged: (value) => setState(() => duration = value)),
              _NumberRow(label: 'Group size', value: group, max: 20, onChanged: (value) => setState(() => group = value)),
              TextField(controller: fare, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Your fare offer in NPR (optional)', prefixIcon: Icon(Icons.payments_outlined))),
              const SizedBox(height: 12),
              TextField(controller: requirements, maxLines: 2, decoration: const InputDecoration(labelText: 'Notes, language, accessibility needs')),
              const SizedBox(height: 18),
              ElevatedButton(
                onPressed: () async {
                  if (pickup.text.trim().isEmpty || destination.text.trim().isEmpty) return;
                  try {
                    await ref.read(apiClientProvider).dio.post(ApiEndpoints.guideRequests, data: {
                      'pickup_name': pickup.text.trim(),
                      'destination_name': destination.text.trim(),
                      'scheduled_at': scheduled.toUtc().toIso8601String(),
                      'duration_hours': duration,
                      'group_size': group,
                      'requirements': requirements.text.trim(),
                      if (fare.text.trim().isNotEmpty) 'proposed_fare': fare.text.trim(),
                    });
                    if (sheetContext.mounted) Navigator.pop(sheetContext, true);
                  } catch (_) {
                    if (sheetContext.mounted) ScaffoldMessenger.of(sheetContext).showSnackBar(const SnackBar(content: Text('Could not create this request. Check the details and retry.')));
                  }
                },
                child: const Text('Find verified guides'),
              ),
            ]),
          ),
        ),
      ),
    );
    pickup.dispose();
    destination.dispose();
    requirements.dispose();
    fare.dispose();
    if (created == true) ref.invalidate(guideRequestsProvider);
  }
}

class _RequestCard extends ConsumerWidget {
  const _RequestCard({required this.request, required this.guideMode, required this.onChanged});
  final Map<String, dynamic> request;
  final bool guideMode;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final offers = (request['offers'] as List? ?? const []).cast<Map>();
    final status = request['status'] as String? ?? '';
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [Expanded(child: Text('${request['pickup_name']}  →  ${request['destination_name']}', style: const TextStyle(fontWeight: FontWeight.bold))), Chip(label: Text(status.replaceAll('_', ' '), style: const TextStyle(fontSize: 10)))]),
          Text('${request['reference']} • ${request['duration_hours']} hours • ${request['group_size']} traveller(s)', style: const TextStyle(color: AppColors.textSecondary)),
          const SizedBox(height: 6),
          Text('Suggested fair fare: NPR ${request['recommended_fare']}', style: const TextStyle(fontWeight: FontWeight.w600)),
          if (request['proposed_fare'] != null) Text('Traveller offer: NPR ${request['proposed_fare']}'),
          if ((request['requirements'] as String? ?? '').isNotEmpty) Text(request['requirements'] as String),
          if (!guideMode && offers.isNotEmpty && ['SEARCHING', 'OFFERED'].contains(status)) ...[
            const Divider(),
            Text('${offers.length} guide offer(s)', style: const TextStyle(fontWeight: FontWeight.bold)),
            for (final offer in offers)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const CircleAvatar(child: Icon(Icons.person_outline)),
                title: Text('${offer['guide_name']} • NPR ${offer['offered_fare']}'),
                subtitle: Text('${offer['eta_minutes']} min away${(offer['message'] as String? ?? '').isEmpty ? '' : ' • ${offer['message']}'}'),
                trailing: ElevatedButton(onPressed: () => _accept(ref, offer['id'] as int), child: const Text('Select')),
              ),
          ],
          if (guideMode && ['SEARCHING', 'OFFERED'].contains(status)) ...[
            const SizedBox(height: 10),
            SizedBox(width: double.infinity, child: ElevatedButton.icon(onPressed: () => _offer(context, ref), icon: const Icon(Icons.local_offer_outlined), label: const Text('Send or update offer'))),
          ],
          if (request['accepted_guide'] != null) ...[
            const Divider(),
            Text('Guide: ${request['accepted_guide_name']} • NPR ${request['final_fare']}', style: const TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Wrap(spacing: 8, runSpacing: 8, children: [
              OutlinedButton.icon(onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ChatRoomPage(room: 'guide-request:${request['id']}', title: request['accepted_guide_name'] as String? ?? 'Guide chat'))), icon: const Icon(Icons.chat_bubble_outline), label: const Text('Chat')),
              if (!guideMode && status == 'ACCEPTED') ElevatedButton.icon(onPressed: () => _pay(context, ref), icon: const Icon(Icons.account_balance_wallet_outlined), label: const Text('Pay')),
              if (!guideMode && status == 'COMPLETED') OutlinedButton.icon(onPressed: () => _review(context, ref), icon: const Icon(Icons.star_outline), label: const Text('Review guide')),
              if (guideMode && ['ACCEPTED', 'EN_ROUTE', 'ARRIVED', 'ACTIVE'].contains(status)) ElevatedButton(onPressed: () => _advance(ref, status), child: Text(_nextLabel(status))),
            ]),
          ],
        ]),
      ),
    );
  }

  Future<void> _accept(WidgetRef ref, int offerId) async {
    await ref.read(apiClientProvider).dio.post('${ApiEndpoints.guideRequests}${request['id']}/accept-offer/', data: {'offer_id': offerId});
    onChanged();
  }

  Future<void> _offer(BuildContext context, WidgetRef ref) async {
    final fare = TextEditingController(text: request['proposed_fare']?.toString() ?? request['recommended_fare']?.toString() ?? '');
    final eta = TextEditingController(text: '15');
    final message = TextEditingController();
    final send = await showDialog<bool>(context: context, builder: (dialogContext) => AlertDialog(
      title: const Text('Send guide offer'),
      content: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(controller: fare, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Fare in NPR')),
        const SizedBox(height: 10),
        TextField(controller: eta, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'ETA in minutes')),
        const SizedBox(height: 10),
        TextField(controller: message, decoration: const InputDecoration(labelText: 'Message (optional)')),
      ]),
      actions: [TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Cancel')), ElevatedButton(onPressed: () => Navigator.pop(dialogContext, true), child: const Text('Send'))],
    ));
    if (send == true) {
      await ref.read(apiClientProvider).dio.post('${ApiEndpoints.guideRequests}${request['id']}/offer/', data: {'offered_fare': fare.text, 'eta_minutes': int.tryParse(eta.text) ?? 15, 'message': message.text});
      onChanged();
    }
    fare.dispose();
    eta.dispose();
    message.dispose();
  }

  Future<void> _advance(WidgetRef ref, String current) async {
    final next = {'ACCEPTED': 'EN_ROUTE', 'EN_ROUTE': 'ARRIVED', 'ARRIVED': 'ACTIVE', 'ACTIVE': 'COMPLETED'}[current];
    await ref.read(apiClientProvider).dio.post('${ApiEndpoints.guideRequests}${request['id']}/transition/', data: {'status': next});
    onChanged();
  }

  Future<void> _pay(BuildContext context, WidgetRef ref) async {
    final paid = await startTargetPayment(context, ref, target: {'guide_request': request['id']});
    if (!context.mounted) return;
    if (paid) onChanged();
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(paid ? 'Payment verified and held securely.' : 'Payment was not completed.')));
  }

  Future<void> _review(BuildContext context, WidgetRef ref) async {
    var rating = 5;
    final comment = TextEditingController();
    final submit = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('Review your guide'),
          content: Column(mainAxisSize: MainAxisSize.min, children: [
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [for (var i = 1; i <= 5; i++) IconButton(onPressed: () => setState(() => rating = i), icon: Icon(i <= rating ? Icons.star : Icons.star_border, color: AppColors.gold))]),
            TextField(controller: comment, maxLines: 3, decoration: const InputDecoration(labelText: 'Share your experience')),
          ]),
          actions: [TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Cancel')), ElevatedButton(onPressed: () => Navigator.pop(dialogContext, true), child: const Text('Submit'))],
        ),
      ),
    );
    if (submit == true) {
      try {
        await ref.read(apiClientProvider).dio.post(ApiEndpoints.reviews, data: {
          'guide_account': request['accepted_guide'], 'rating': rating,
          'title': 'On-demand guide trip', 'comment': comment.text.trim(),
        });
        if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Review submitted for moderation.')));
      } catch (_) {
        if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('You may already have reviewed this guide.')));
      }
    }
    comment.dispose();
  }

  static String _nextLabel(String status) => switch (status) { 'ACCEPTED' => 'Start travel', 'EN_ROUTE' => 'Mark arrived', 'ARRIVED' => 'Start trip', _ => 'Complete trip' };
}

class _NumberRow extends StatelessWidget {
  const _NumberRow({required this.label, required this.value, required this.max, required this.onChanged});
  final String label;
  final int value;
  final int max;
  final ValueChanged<int> onChanged;
  @override
  Widget build(BuildContext context) => Row(children: [Expanded(child: Text(label)), IconButton(onPressed: value > 1 ? () => onChanged(value - 1) : null, icon: const Icon(Icons.remove_circle_outline)), Text('$value'), IconButton(onPressed: value < max ? () => onChanged(value + 1) : null, icon: const Icon(Icons.add_circle_outline))]);
}
