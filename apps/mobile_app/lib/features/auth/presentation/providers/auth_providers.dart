import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/api/api_client.dart';
import '../../../../core/storage/token_storage.dart';
import '../../data/datasources/auth_remote_datasource.dart';
import '../../data/repositories/auth_repository_impl.dart';
import '../../domain/repositories/auth_repository.dart';
import 'auth_state.dart';

// ---- Dependency injection (clean architecture wiring) ----------------------

final tokenStorageProvider = Provider<TokenStorage>((ref) => TokenStorage());

final apiClientProvider = Provider<ApiClient>(
  (ref) => ApiClient(tokenStorage: ref.watch(tokenStorageProvider)),
);

final authRemoteDataSourceProvider = Provider<AuthRemoteDataSource>(
  (ref) => AuthRemoteDataSource(ref.watch(apiClientProvider).dio),
);

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepositoryImpl(
    ref.watch(authRemoteDataSourceProvider),
    ref.watch(tokenStorageProvider),
  ),
);

// ---- Auth controller -------------------------------------------------------

class AuthController extends Notifier<AuthState> {
  AuthRepository get _repo => ref.read(authRepositoryProvider);

  @override
  AuthState build() => const AuthInitial();

  /// Called on splash: restores the session if a valid token is stored.
  Future<void> bootstrap() async {
    state = const AuthLoading();
    final (_, user) = await _repo.currentUser();
    state = user != null ? AuthAuthenticated(user) : const AuthUnauthenticated();
  }

  Future<void> login({required String email, required String password}) async {
    state = const AuthLoading();
    final (failure, user) = await _repo.login(email: email, password: password);
    state = user != null
        ? AuthAuthenticated(user)
        : AuthFailure(failure?.message ?? 'Login failed');
  }

  Future<void> register({
    required String fullName,
    required String email,
    required String password,
    String? phone,
    String role = 'TOURIST',
    String? licenseNumber,
    String? bio,
  }) async {
    state = const AuthLoading();
    final (failure, user) = await _repo.register(
      fullName: fullName,
      email: email,
      password: password,
      phoneNumber: phone,
      role: role,
      licenseNumber: licenseNumber,
      bio: bio,
    );
    state = user != null
        ? AuthAuthenticated(user)
        : AuthFailure(failure?.message ?? 'Sign up failed');
  }

  Future<void> logout() async {
    await _repo.logout();
    state = const AuthUnauthenticated();
  }
}

final authControllerProvider =
    NotifierProvider<AuthController, AuthState>(AuthController.new);
