import 'package:dio/dio.dart';

import '../../../../core/error/api_error_mapper.dart';
import '../../../../core/error/failures.dart';
import '../../../../core/storage/token_storage.dart';
import '../../domain/entities/auth_user.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_remote_datasource.dart';

class AuthRepositoryImpl implements AuthRepository {
  const AuthRepositoryImpl(this._remote, this._tokenStorage);

  final AuthRemoteDataSource _remote;
  final TokenStorage _tokenStorage;

  @override
  Future<(Failure?, AuthUser?)> login({
    required String email,
    required String password,
  }) async {
    try {
      final tokens = await _remote.login(email: email, password: password);
      await _tokenStorage.saveTokens(access: tokens.access, refresh: tokens.refresh);
      final user = await _remote.currentUser();
      return (null, user.toEntity());
    } on DioException catch (e) {
      return (mapDioError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  @override
  Future<(Failure?, AuthUser?)> register({
    required String fullName,
    required String email,
    required String password,
    String? phoneNumber,
    required String role,
    String? licenseNumber,
    String? bio,
  }) async {
    try {
      final parts = fullName.trim().split(RegExp(r'\s+'));
      final firstName = parts.isNotEmpty ? parts.first : fullName;
      final lastName = parts.length > 1 ? parts.sublist(1).join(' ') : '';
      await _remote.register(
        username: email,
        email: email,
        password: password,
        firstName: firstName,
        lastName: lastName,
        phoneNumber: phoneNumber,
        role: role,
        licenseNumber: licenseNumber,
        bio: bio,
      );
      // Smooth UX: sign the user straight in after a successful registration.
      return login(email: email, password: password);
    } on DioException catch (e) {
      return (mapDioError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  @override
  Future<(Failure?, AuthUser?)> currentUser() async {
    try {
      final token = await _tokenStorage.getAccessToken();
      if (token == null || token.isEmpty) return (null, null);
      final user = await _remote.currentUser();
      return (null, user.toEntity());
    } on DioException catch (e) {
      return (mapDioError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  @override
  Future<void> logout() => _tokenStorage.clear();

}
