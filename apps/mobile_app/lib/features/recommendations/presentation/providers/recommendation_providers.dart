import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/presentation/providers/auth_providers.dart';
import '../../../destinations/domain/entities/destination.dart';
import '../../../guides/domain/entities/guide.dart';
import '../../data/datasources/recommendation_remote_datasource.dart';
import '../../data/repositories/recommendation_repository_impl.dart';
import '../../domain/repositories/recommendation_repository.dart';

// ---- Dependency injection (clean architecture wiring) ----------------------

final recommendationRemoteDataSourceProvider =
    Provider<RecommendationRemoteDataSource>(
  (ref) => RecommendationRemoteDataSource(ref.watch(apiClientProvider).dio),
);

final recommendationRepositoryProvider = Provider<RecommendationRepository>(
  (ref) => RecommendationRepositoryImpl(
    ref.watch(recommendationRemoteDataSourceProvider),
  ),
);

// ---- Screen state ----------------------------------------------------------

/// Personalised trek suggestions. Exposed as [AsyncValue] for free
/// loading / error / data states on the Home screen.
final recommendedRoutesProvider =
    FutureProvider.autoDispose<List<Destination>>((ref) async {
  final (failure, data) =
      await ref.watch(recommendationRepositoryProvider).getRecommendedRoutes();
  if (failure != null) throw failure;
  return data ?? const [];
});

/// Personalised guide suggestions.
final recommendedGuidesProvider =
    FutureProvider.autoDispose<List<Guide>>((ref) async {
  final (failure, data) =
      await ref.watch(recommendationRepositoryProvider).getRecommendedGuides();
  if (failure != null) throw failure;
  return data ?? const [];
});
