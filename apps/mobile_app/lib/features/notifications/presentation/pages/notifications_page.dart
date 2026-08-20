import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../../core/api/api_endpoints.dart';
import '../../../auth/presentation/providers/auth_providers.dart';

final notificationsProvider = FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final response = await ref.watch(apiClientProvider).dio.get(ApiEndpoints.notifications);
  final data = response.data;
  final rows = data is Map ? data['results'] as List? ?? const [] : data as List? ?? const [];
  return rows.cast<Map>().map((row) => Map<String, dynamic>.from(row)).toList();
});

class NotificationsPage extends ConsumerWidget {
  const NotificationsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifications = ref.watch(notificationsProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          TextButton(
            onPressed: () async {
              await ref.read(apiClientProvider).dio.post('${ApiEndpoints.notifications}read_all/');
              ref.invalidate(notificationsProvider);
            },
            child: const Text('Read all'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(notificationsProvider.future),
        child: notifications.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (_, _) => ListView(children: const [
            SizedBox(height: 120),
            Center(child: Text('Could not load notifications. Pull to retry.')),
          ]),
          data: (items) => items.isEmpty
              ? ListView(children: const [
                  SizedBox(height: 120),
                  Icon(Icons.notifications_none, size: 48, color: AppColors.textSecondary),
                  SizedBox(height: 12),
                  Center(child: Text('You are all caught up.')),
                ])
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 10),
                  itemBuilder: (context, index) {
                    final item = items[index];
                    return Card(
                      color: item['is_read'] == true
                          ? AppColors.surface
                          : AppColors.primary.withValues(alpha: .06),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: AppColors.primary.withValues(alpha: .12),
                          child: Icon(_iconFor(item['kind'] as String?), color: AppColors.primary),
                        ),
                        title: Text(item['title'] as String? ?? 'GuideU update'),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if ((item['body'] as String? ?? '').isNotEmpty) Text(item['body'] as String),
                            const SizedBox(height: 4),
                            Text(_formatDate(item['created_at'] as String?), style: const TextStyle(fontSize: 11)),
                          ],
                        ),
                        isThreeLine: true,
                        onTap: item['is_read'] == true
                            ? null
                            : () async {
                                await ref.read(apiClientProvider).dio.post(
                                  '${ApiEndpoints.notifications}${item['id']}/read/',
                                );
                                ref.invalidate(notificationsProvider);
                              },
                      ),
                    );
                  },
                ),
        ),
      ),
    );
  }

  static IconData _iconFor(String? kind) => switch (kind) {
        'PAYMENT' => Icons.account_balance_wallet_outlined,
        'SCAM' || 'SYSTEM' => Icons.shield_outlined,
        'REVIEW' => Icons.star_outline,
        _ => Icons.calendar_month_outlined,
      };

  static String _formatDate(String? value) {
    final date = DateTime.tryParse(value ?? '')?.toLocal();
    return date == null ? '' : DateFormat('MMM d, h:mm a').format(date);
  }
}
