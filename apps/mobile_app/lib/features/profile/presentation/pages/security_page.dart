import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../../core/utils/validators.dart';
import '../../../auth/presentation/providers/auth_providers.dart';

class SecurityPage extends ConsumerStatefulWidget {
  const SecurityPage({super.key});
  @override
  ConsumerState<SecurityPage> createState() => _SecurityPageState();
}

class _SecurityPageState extends ConsumerState<SecurityPage> {
  final _formKey = GlobalKey<FormState>();
  final _current = TextEditingController();
  final _next = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _current.dispose();
    _next.dispose();
    super.dispose();
  }

  Future<void> _changePassword() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _loading = true);
    try {
      await ref.read(apiClientProvider).dio.post(ApiEndpoints.changePassword, data: {
        'current_password': _current.text,
        'new_password': _next.text,
      });
      if (!mounted) return;
      _current.clear();
      _next.clear();
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Password changed successfully.')));
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not change password. Check your current password.')));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Security')),
        body: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              const ListTile(
                contentPadding: EdgeInsets.zero,
                leading: Icon(Icons.verified_user_outlined),
                title: Text('Secure account'),
                subtitle: Text('Use a unique password with letters, numbers, and symbols.'),
              ),
              const SizedBox(height: 12),
              TextFormField(controller: _current, obscureText: true, decoration: const InputDecoration(labelText: 'Current password'), validator: (value) => Validators.required(value, 'Current password')),
              const SizedBox(height: 14),
              TextFormField(controller: _next, obscureText: true, decoration: const InputDecoration(labelText: 'New password'), validator: Validators.password),
              const SizedBox(height: 20),
              ElevatedButton(onPressed: _loading ? null : _changePassword, child: Text(_loading ? 'Updating…' : 'Change password')),
            ],
          ),
        ),
      );
}
