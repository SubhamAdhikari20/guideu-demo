import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/presentation/providers/auth_providers.dart';
import '../../data/datasources/anti_scam_remote_datasource.dart';
import '../../data/repositories/anti_scam_repository_impl.dart';
import '../../domain/entities/price_check_result.dart';
import '../../domain/repositories/anti_scam_repository.dart';

// ---- Dependency injection (clean architecture wiring) ----------------------

final antiScamRemoteDataSourceProvider = Provider<AntiScamRemoteDataSource>(
  (ref) => AntiScamRemoteDataSource(ref.watch(apiClientProvider).dio),
);

final antiScamRepositoryProvider = Provider<AntiScamRepository>(
  (ref) => AntiScamRepositoryImpl(ref.watch(antiScamRemoteDataSourceProvider)),
);

// ---- Screen state ----------------------------------------------------------

/// Region names for the dropdowns (from the catalog).
final regionNamesProvider = FutureProvider.autoDispose<List<String>>((ref) async {
  final (failure, data) =
      await ref.watch(antiScamRepositoryProvider).getRegionNames();
  if (failure != null) throw failure;
  return data ?? const [];
});

/// Immutable query for the price check — value equality makes it a safe
/// `family` key, so the same inputs reuse the same result.
class PriceCheckQuery {
  const PriceCheckQuery({
    required this.serviceType,
    required this.quotedPriceNpr,
    this.region,
    this.season,
  });

  final String serviceType;
  final int quotedPriceNpr;
  final String? region;
  final String? season;

  @override
  bool operator ==(Object other) =>
      other is PriceCheckQuery &&
      other.serviceType == serviceType &&
      other.quotedPriceNpr == quotedPriceNpr &&
      other.region == region &&
      other.season == season;

  @override
  int get hashCode => Object.hash(serviceType, quotedPriceNpr, region, season);
}

/// Runs the fair-price check for a given query. Watched only after the user
/// submits the form, so the request fires on demand.
final priceCheckProvider = FutureProvider.autoDispose
    .family<PriceCheckResult, PriceCheckQuery>((ref, query) async {
  final (failure, data) = await ref.watch(antiScamRepositoryProvider).checkPrice(
        serviceType: query.serviceType,
        quotedPriceNpr: query.quotedPriceNpr,
        region: query.region,
        season: query.season,
      );
  if (failure != null) throw failure;
  return data!;
});
