import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/presentation/providers/auth_providers.dart';
import '../../data/datasources/workspace_remote_datasource.dart';
import '../../data/repositories/workspace_repository_impl.dart';
import '../../domain/entities/trip.dart';
import '../../domain/repositories/workspace_repository.dart';

// ---- Dependency injection (clean architecture wiring) ----------------------

final workspaceRemoteDataSourceProvider = Provider<WorkspaceRemoteDataSource>(
  (ref) => WorkspaceRemoteDataSource(ref.watch(apiClientProvider).dio),
);

final workspaceRepositoryProvider = Provider<WorkspaceRepository>(
  (ref) => WorkspaceRepositoryImpl(ref.watch(workspaceRemoteDataSourceProvider)),
);

// ---- Screen state ----------------------------------------------------------

/// All of my trips.
final tripsProvider = FutureProvider.autoDispose<List<TravelTrip>>((ref) async {
  final (failure, data) = await ref.watch(workspaceRepositoryProvider).getTrips();
  if (failure != null) throw failure;
  return data ?? const [];
});

/// One trip with its items, keyed by id.
final tripDetailProvider =
    FutureProvider.autoDispose.family<TravelTrip, int>((ref, id) async {
  final (failure, data) = await ref.watch(workspaceRepositoryProvider).getTrip(id);
  if (failure != null) throw failure;
  return data!;
});
