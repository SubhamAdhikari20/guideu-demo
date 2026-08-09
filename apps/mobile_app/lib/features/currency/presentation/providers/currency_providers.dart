import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/presentation/providers/auth_providers.dart';
import '../../data/datasources/currency_remote_datasource.dart';

final currencyRemoteDataSourceProvider = Provider<CurrencyRemoteDataSource>(
  (ref) => CurrencyRemoteDataSource(ref.watch(apiClientProvider).dio),
);

/// NPR-based exchange rates, fetched from the backend (cached server-side).
final currencyRatesProvider =
    FutureProvider.autoDispose<Map<String, double>>((ref) async {
  return ref.watch(currencyRemoteDataSourceProvider).getRates();
});

/// The tourist's preferred display currency (kept for the session). Prices are
/// always shown in NPR, with this currency in brackets when it isn't NPR.
class CurrencyPreference extends Notifier<String> {
  @override
  String build() => 'NPR';

  void set(String currency) => state = currency;
}

final currencyPreferenceProvider =
    NotifierProvider<CurrencyPreference, String>(CurrencyPreference.new);

/// Common symbols for the supported currencies (falls back to the code).
const currencySymbols = <String, String>{
  'NPR': 'Rs. ', 'USD': '\$', 'EUR': '€', 'GBP': '£',
  'INR': '₹', 'AUD': 'A\$', 'JPY': '¥',
};
