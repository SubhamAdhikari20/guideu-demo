import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/currency_providers.dart';

/// Reusable price label. Always shows NPR; when the tourist has picked another
/// display currency it appends the converted value, e.g. "Rs. 5,000 (≈ $37.50)".
class PriceDisplay extends ConsumerWidget {
  const PriceDisplay({required this.amountNpr, this.style, super.key});

  final double amountNpr;
  final TextStyle? style;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final base = 'Rs. ${amountNpr.toStringAsFixed(0)}';
    final pref = ref.watch(currencyPreferenceProvider);
    if (pref == 'NPR') return Text(base, style: style);

    final rates = ref.watch(currencyRatesProvider);
    return rates.maybeWhen(
      data: (r) {
        final rate = r[pref];
        if (rate == null) return Text(base, style: style);
        final symbol = currencySymbols[pref] ?? '$pref ';
        final converted = (amountNpr * rate).toStringAsFixed(2);
        return Text('$base (≈ $symbol$converted)', style: style);
      },
      orElse: () => Text(base, style: style),
    );
  }
}
