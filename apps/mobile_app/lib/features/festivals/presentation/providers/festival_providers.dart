import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/presentation/providers/auth_providers.dart';
import '../../data/datasources/festival_remote_datasource.dart';
import '../../data/repositories/festival_repository_impl.dart';
import '../../domain/entities/festival.dart';
import '../../domain/repositories/festival_repository.dart';

// ---- Dependency injection (clean architecture wiring) ----------------------

final festivalRemoteDataSourceProvider = Provider<FestivalRemoteDataSource>(
  (ref) => FestivalRemoteDataSource(ref.watch(apiClientProvider).dio),
);

final festivalRepositoryProvider = Provider<FestivalRepository>(
  (ref) => FestivalRepositoryImpl(ref.watch(festivalRemoteDataSourceProvider)),
);

// ---- Screen state ----------------------------------------------------------

/// The next 12 months of festivals, grouped by month. Exposed as [AsyncValue]
/// so the hub gets loading / error / data states for free.
final upcomingFestivalsProvider =
    FutureProvider.autoDispose<List<FestivalMonth>>((ref) async {
  final (failure, data) =
      await ref.watch(festivalRepositoryProvider).getUpcoming(months: 12);
  if (failure != null) throw failure;
  return data ?? const [];
});
