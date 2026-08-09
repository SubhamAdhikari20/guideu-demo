import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/presentation/providers/auth_providers.dart';
import '../../data/datasources/chat_remote_datasource.dart';
import '../../data/repositories/chat_repository_impl.dart';
import '../../domain/entities/chat_thread.dart';
import '../../domain/repositories/chat_repository.dart';

// ---- Dependency injection (clean architecture wiring) ----------------------

final chatRemoteDataSourceProvider = Provider<ChatRemoteDataSource>(
  (ref) => ChatRemoteDataSource(ref.watch(apiClientProvider).dio),
);

final chatRepositoryProvider = Provider<ChatRepository>(
  (ref) => ChatRepositoryImpl(ref.watch(chatRemoteDataSourceProvider)),
);

// ---- Screen state ----------------------------------------------------------

/// The chat inbox — threads the current user is part of.
final chatThreadsProvider = FutureProvider.autoDispose<List<ChatThread>>((ref) async {
  final (failure, data) = await ref.watch(chatRepositoryProvider).getThreads();
  if (failure != null) throw failure;
  return data ?? const [];
});
