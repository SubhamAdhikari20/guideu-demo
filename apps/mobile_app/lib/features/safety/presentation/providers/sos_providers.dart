import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/presentation/providers/auth_providers.dart';
import '../../data/datasources/sos_remote_datasource.dart';

final sosRemoteDataSourceProvider = Provider<SosRemoteDataSource>(
  (ref) => SosRemoteDataSource(ref.watch(apiClientProvider).dio),
);
