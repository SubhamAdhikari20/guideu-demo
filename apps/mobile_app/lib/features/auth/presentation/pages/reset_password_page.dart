import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../app/routes/app_router.dart';
import '../../../../core/api/api_endpoints.dart';
import '../../../../core/utils/validators.dart';
import '../providers/auth_providers.dart';

class ResetPasswordPage extends ConsumerStatefulWidget {
  const ResetPasswordPage({this.uid = '', this.token = '', super.key});
  final String uid;
  final String token;
  @override
  ConsumerState<ResetPasswordPage> createState() => _ResetPasswordPageState();
}

class _ResetPasswordPageState extends ConsumerState<ResetPasswordPage> {
  late final TextEditingController _uid;
  late final TextEditingController _token;
  final _password = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  var _loading = false;

  @override
  void initState() {
    super.initState();
    _uid = TextEditingController(text: widget.uid);
    _token = TextEditingController(text: widget.token);
  }

  @override
  void dispose() {
    _uid.dispose(); _token.dispose(); _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _loading = true);
    try {
      await ref.read(apiClientProvider).dio.post(ApiEndpoints.passwordResetConfirm, data: {
        'uid': _uid.text.trim(), 'token': _token.text.trim(), 'new_password': _password.text,
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Password reset. You can now sign in.')));
      context.go(AppRoutes.login);
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('The reset code is invalid or expired.')));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Reset password')),
    body: Form(key: _formKey, child: ListView(padding: const EdgeInsets.all(24), children: [
      const Text('Enter the account code and reset code from your GuideU email.'),
      const SizedBox(height: 18),
      TextFormField(controller: _uid, decoration: const InputDecoration(labelText: 'Account code'), validator: (value) => Validators.required(value, 'Account code')),
      const SizedBox(height: 12),
      TextFormField(controller: _token, decoration: const InputDecoration(labelText: 'Reset code'), validator: (value) => Validators.required(value, 'Reset code')),
      const SizedBox(height: 12),
      TextFormField(controller: _password, obscureText: true, decoration: const InputDecoration(labelText: 'New password'), validator: Validators.password),
      const SizedBox(height: 20),
      ElevatedButton(onPressed: _loading ? null : _submit, child: Text(_loading ? 'Resetting…' : 'Set new password')),
    ])),
  );
}
