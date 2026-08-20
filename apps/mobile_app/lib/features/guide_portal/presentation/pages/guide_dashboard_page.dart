import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../../core/api/api_endpoints.dart';
import '../../../auth/presentation/providers/auth_providers.dart';
import '../../../auth/presentation/providers/auth_state.dart';
import '../../../notifications/presentation/pages/notifications_page.dart';

final guideProfileProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final response = await ref.watch(apiClientProvider).dio.get(ApiEndpoints.guideProfile);
  return Map<String, dynamic>.from(response.data as Map);
});

final guideEarningsProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final response = await ref.watch(apiClientProvider).dio.get('${ApiEndpoints.guideRequests}earnings/');
  return Map<String, dynamic>.from(response.data as Map);
});

class GuideDashboardPage extends ConsumerWidget {
  const GuideDashboardPage({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final user = auth is AuthAuthenticated ? auth.user : null;
    final profile = ref.watch(guideProfileProvider);
    final earnings = ref.watch(guideEarningsProvider).value;
    return Scaffold(
      appBar: AppBar(
        title: const Text('GuideU Guide'),
        actions: [IconButton(onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const NotificationsPage())), icon: const Icon(Icons.notifications_none))],
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(guideProfileProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text('Namaste, ${user?.fullName ?? 'Guide'}', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            Text(user?.isGuideVerified == true ? 'Verified GuideU partner' : 'Verification pending', style: TextStyle(color: user?.isGuideVerified == true ? AppColors.primary : AppColors.gold)),
            const SizedBox(height: 18),
            profile.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (_, _) => const Card(child: Padding(padding: EdgeInsets.all(16), child: Text('Could not load your guide profile.'))),
              data: (data) {
                final available = data['availability'] == 'AVAILABLE';
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Row(children: [
                        CircleAvatar(radius: 26, backgroundColor: available ? AppColors.primary.withValues(alpha: .14) : AppColors.inputFill, child: Icon(available ? Icons.online_prediction : Icons.offline_bolt_outlined, color: available ? AppColors.primary : AppColors.textSecondary)),
                        const SizedBox(width: 12),
                        const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Accept nearby requests', style: TextStyle(fontWeight: FontWeight.bold)), Text('Tourists see offers only from verified, available guides.', style: TextStyle(fontSize: 12, color: AppColors.textSecondary))])),
                        Switch(value: available, onChanged: user?.isGuideVerified == true ? (value) => _availability(ref, value) : null),
                      ]),
                      const Divider(),
                      Text(data['bio'] as String? ?? 'Add a bio from your profile to help travellers choose you.'),
                      const SizedBox(height: 8),
                      Text('Licence: ${data['license_number'] ?? 'Not provided'}', style: const TextStyle(color: AppColors.textSecondary)),
                    ]),
                  ),
                );
              },
            ),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(child: _Metric(icon: Icons.payments_outlined, label: 'Released earnings', value: 'NPR ${earnings?['released_total'] ?? '0.00'}')),
              const SizedBox(width: 10),
              Expanded(child: _Metric(icon: Icons.hourglass_top, label: 'In escrow', value: 'NPR ${earnings?['pending_total'] ?? '0.00'}')),
            ]),
            const SizedBox(height: 10),
            Card(child: ListTile(leading: const Icon(Icons.star, color: AppColors.gold), title: Text('${earnings?['average_rating'] ?? 0} average rating'), subtitle: Text('${earnings?['review_count'] ?? 0} approved traveller review(s)'))),
            const SizedBox(height: 16),
            const Card(child: ListTile(leading: Icon(Icons.tips_and_updates_outlined, color: AppColors.gold), title: Text('How offers work'), subtitle: Text('Review the pickup, destination, group, fair-price benchmark, and traveller notes before bidding. The traveller compares price, ETA, and profile before selecting a guide.'))),
          ],
        ),
      ),
    );
  }

  Future<void> _availability(WidgetRef ref, bool value) async {
    await ref.read(apiClientProvider).dio.patch(ApiEndpoints.guideProfile, data: {'availability': value ? 'AVAILABLE' : 'OFFLINE'});
    ref.invalidate(guideProfileProvider);
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Icon(icon, color: AppColors.primary), const SizedBox(height: 8), Text(label, style: const TextStyle(fontWeight: FontWeight.bold)), Text(value, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary))])));
}
