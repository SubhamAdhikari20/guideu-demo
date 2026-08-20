import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../auth/presentation/providers/auth_providers.dart';

final preferencesProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final response = await ref.watch(apiClientProvider).dio.get(ApiEndpoints.preferences);
  return Map<String, dynamic>.from(response.data as Map);
});

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final preferences = ref.watch(preferencesProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: preferences.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => const Center(child: Text('Could not load settings.')),
        data: (data) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Text('Preferences', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            ListTile(
              leading: const Icon(Icons.language),
              title: const Text('Language'),
              trailing: DropdownButton<String>(
                value: data['language'] as String? ?? 'en',
                items: const [
                  DropdownMenuItem(value: 'en', child: Text('English')),
                  DropdownMenuItem(value: 'ne', child: Text('नेपाली')),
                ],
                onChanged: (value) => _update(ref, {'language': value}),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.currency_exchange),
              title: const Text('Display currency'),
              trailing: DropdownButton<String>(
                value: data['currency'] as String? ?? 'NPR',
                items: const [
                  DropdownMenuItem(value: 'NPR', child: Text('NPR')),
                  DropdownMenuItem(value: 'USD', child: Text('USD')),
                  DropdownMenuItem(value: 'EUR', child: Text('EUR')),
                ],
                onChanged: (value) => _update(ref, {'currency': value}),
              ),
            ),
            const Divider(),
            const Text('Notifications', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            _SettingSwitch(label: 'Push notifications', value: data['push_notifications'] == true, onChanged: (value) => _update(ref, {'push_notifications': value})),
            _SettingSwitch(label: 'Email notifications', value: data['email_notifications'] == true, onChanged: (value) => _update(ref, {'email_notifications': value})),
            _SettingSwitch(label: 'Booking updates', value: data['booking_notifications'] == true, onChanged: (value) => _update(ref, {'booking_notifications': value})),
            _SettingSwitch(label: 'Festival reminders', value: data['festival_notifications'] == true, onChanged: (value) => _update(ref, {'festival_notifications': value})),
            _SettingSwitch(label: 'Safety alerts', value: data['safety_notifications'] == true, onChanged: (value) => _update(ref, {'safety_notifications': value})),
            const Divider(),
            _SettingSwitch(label: 'Private profile', value: data['profile_is_private'] == true, onChanged: (value) => _update(ref, {'profile_is_private': value})),
          ],
        ),
      ),
    );
  }

  Future<void> _update(WidgetRef ref, Map<String, dynamic> data) async {
    await ref.read(apiClientProvider).dio.patch(ApiEndpoints.preferences, data: data);
    ref.invalidate(preferencesProvider);
  }
}

class _SettingSwitch extends StatelessWidget {
  const _SettingSwitch({required this.label, required this.value, required this.onChanged});
  final String label;
  final bool value;
  final ValueChanged<bool> onChanged;
  @override
  Widget build(BuildContext context) => SwitchListTile(title: Text(label), value: value, onChanged: onChanged);
}
