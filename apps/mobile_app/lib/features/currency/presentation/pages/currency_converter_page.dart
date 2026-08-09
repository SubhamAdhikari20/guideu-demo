import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/theme/app_colors.dart';
import '../providers/currency_providers.dart';

/// Converts an amount from NPR to a chosen currency using the live backend
/// rates, and lets the tourist set their default display currency.
class CurrencyConverterPage extends ConsumerStatefulWidget {
  const CurrencyConverterPage({super.key});

  @override
  ConsumerState<CurrencyConverterPage> createState() => _CurrencyConverterPageState();
}

class _CurrencyConverterPageState extends ConsumerState<CurrencyConverterPage> {
  final _amount = TextEditingController(text: '5000');
  String _to = 'USD';

  @override
  void dispose() {
    _amount.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final rates = ref.watch(currencyRatesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Currency Converter')),
      body: rates.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Could not load exchange rates.',
                  style: TextStyle(color: AppColors.textSecondary)),
              const SizedBox(height: 8),
              OutlinedButton(
                onPressed: () => ref.invalidate(currencyRatesProvider),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (r) {
          final currencies = r.keys.toList()..sort();
          final amount = double.tryParse(_amount.text.trim()) ?? 0;
          final rate = r[_to] ?? 1.0;
          final converted = (amount * rate).toStringAsFixed(2);
          final symbol = currencySymbols[_to] ?? '$_to ';

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              TextField(
                controller: _amount,
                keyboardType: TextInputType.number,
                onChanged: (_) => setState(() {}),
                decoration: const InputDecoration(labelText: 'Amount in NPR', prefixText: 'Rs. '),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: currencies.contains(_to) ? _to : currencies.first,
                decoration: const InputDecoration(labelText: 'Convert to'),
                items: [
                  for (final c in currencies) DropdownMenuItem(value: c, child: Text(c)),
                ],
                onChanged: (v) => setState(() => _to = v ?? _to),
              ),
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  children: [
                    Text('$symbol$converted',
                        style: const TextStyle(
                            fontSize: 28, fontWeight: FontWeight.bold, color: AppColors.primary)),
                    const SizedBox(height: 4),
                    Text('Rs. ${amount.toStringAsFixed(0)} = $symbol$converted',
                        style: const TextStyle(color: AppColors.textSecondary)),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              OutlinedButton.icon(
                onPressed: () {
                  ref.read(currencyPreferenceProvider.notifier).set(_to);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Prices will now also show in $_to.')),
                  );
                },
                icon: const Icon(Icons.check),
                label: Text('Show prices in $_to across the app'),
              ),
            ],
          );
        },
      ),
    );
  }
}
