import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../auth/presentation/providers/auth_providers.dart';
import '../../../auth/presentation/providers/auth_state.dart';

class EditProfilePage extends ConsumerStatefulWidget {
  const EditProfilePage({super.key});
  @override
  ConsumerState<EditProfilePage> createState() => _EditProfilePageState();
}

class _EditProfilePageState extends ConsumerState<EditProfilePage> {
  final _firstName = TextEditingController();
  final _lastName = TextEditingController();
  final _phone = TextEditingController();
  final _bio = TextEditingController();
  final _dailyRate = TextEditingController();
  var _loading = true;
  var _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final me = await ref.read(apiClientProvider).dio.get(ApiEndpoints.me);
      final data = Map<String, dynamic>.from(me.data as Map);
      _firstName.text = data['first_name'] as String? ?? '';
      _lastName.text = data['last_name'] as String? ?? '';
      _phone.text = data['phone_number'] as String? ?? '';
      if (data['role'] == 'GUIDE') {
        final profile = await ref.read(apiClientProvider).dio.get(ApiEndpoints.guideProfile);
        final guide = Map<String, dynamic>.from(profile.data as Map);
        _bio.text = guide['bio'] as String? ?? '';
        _dailyRate.text = guide['daily_rate_npr']?.toString() ?? '';
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _firstName.dispose();
    _lastName.dispose();
    _phone.dispose();
    _bio.dispose();
    _dailyRate.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await ref.read(apiClientProvider).dio.patch(ApiEndpoints.me, data: {
        'first_name': _firstName.text.trim(),
        'last_name': _lastName.text.trim(),
        'phone_number': _phone.text.trim(),
      });
      final auth = ref.read(authControllerProvider);
      if (auth is AuthAuthenticated && auth.user.isGuide) {
        await ref.read(apiClientProvider).dio.patch(ApiEndpoints.guideProfile, data: {
          'bio': _bio.text.trim(),
          if (_dailyRate.text.trim().isNotEmpty) 'daily_rate_npr': _dailyRate.text.trim(),
        });
      }
      await ref.read(authControllerProvider.notifier).bootstrap();
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Profile updated.')));
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not update profile.')));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final isGuide = auth is AuthAuthenticated && auth.user.isGuide;
    return Scaffold(
      appBar: AppBar(title: const Text('Edit profile')),
      body: _loading ? const Center(child: CircularProgressIndicator()) : ListView(
        padding: const EdgeInsets.all(20),
        children: [
          TextField(controller: _firstName, decoration: const InputDecoration(labelText: 'First name')),
          const SizedBox(height: 12),
          TextField(controller: _lastName, decoration: const InputDecoration(labelText: 'Last name')),
          const SizedBox(height: 12),
          TextField(controller: _phone, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Phone number')),
          if (isGuide) ...[
            const SizedBox(height: 12),
            TextField(controller: _bio, maxLines: 4, decoration: const InputDecoration(labelText: 'Guide bio')),
            const SizedBox(height: 12),
            TextField(controller: _dailyRate, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Daily rate (NPR)')),
          ],
          const SizedBox(height: 20),
          ElevatedButton(onPressed: _saving ? null : _save, child: Text(_saving ? 'Saving…' : 'Save changes')),
        ],
      ),
    );
  }
}
