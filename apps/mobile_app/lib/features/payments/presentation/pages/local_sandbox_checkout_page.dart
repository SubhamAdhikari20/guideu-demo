import 'package:flutter/material.dart';

import '../../../../app/theme/app_colors.dart';
import '../../domain/entities/payment.dart';

/// A safe local checkout used by the Docker demo when PAYMENT_MODE=demo.
///
/// It deliberately never collects real wallet credentials. Provider-hosted
/// checkout is still used when the backend runs in sandbox or live mode.
class LocalSandboxCheckoutPage extends StatefulWidget {
  const LocalSandboxCheckoutPage({required this.payment, super.key});

  final Payment payment;

  @override
  State<LocalSandboxCheckoutPage> createState() =>
      _LocalSandboxCheckoutPageState();
}

class _LocalSandboxCheckoutPageState extends State<LocalSandboxCheckoutPage> {
  final _wallet = TextEditingController(text: '9800000000');
  final _pin = TextEditingController(text: '1234');
  bool _processing = false;

  @override
  void dispose() {
    _wallet.dispose();
    _pin.dispose();
    super.dispose();
  }

  Future<void> _confirm() async {
    if (_wallet.text.trim().isEmpty || _pin.text.trim().length < 4) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Enter the provided test wallet and PIN.'),
        ),
      );
      return;
    }
    setState(() => _processing = true);
    await Future<void>.delayed(const Duration(milliseconds: 650));
    if (mounted) Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final gateway = widget.payment.gateway.toUpperCase();
    final isKhalti = gateway == 'KHALTI';
    final brand = isKhalti ? const Color(0xff5c2d91) : const Color(0xff60bb46);
    final name = isKhalti ? 'Khalti' : 'eSewa';

    return Scaffold(
      appBar: AppBar(title: Text('$name local sandbox')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: brand,
              borderRadius: BorderRadius.circular(18),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 18),
                const Text(
                  'GuideU test payment',
                  style: TextStyle(color: Colors.white70),
                ),
                Text(
                  '${widget.payment.currency} ${widget.payment.amount.toStringAsFixed(2)}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.gold.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text(
              'Local sandbox only. No money is charged and these are not real wallet credentials.',
            ),
          ),
          const SizedBox(height: 18),
          TextField(
            controller: _wallet,
            keyboardType: TextInputType.phone,
            decoration: const InputDecoration(
              labelText: 'Test wallet number',
              prefixIcon: Icon(Icons.phone_android),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _pin,
            obscureText: true,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Test PIN',
              prefixIcon: Icon(Icons.lock_outline),
            ),
          ),
          const SizedBox(height: 22),
          ElevatedButton.icon(
            onPressed: _processing ? null : _confirm,
            icon: _processing
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.verified_user_outlined),
            label: Text(
              _processing
                  ? 'Verifying test payment...'
                  : 'Confirm test payment',
            ),
          ),
          const SizedBox(height: 10),
          TextButton(
            onPressed: _processing
                ? null
                : () => Navigator.of(context).pop(false),
            child: const Text('Cancel payment'),
          ),
        ],
      ),
    );
  }
}
