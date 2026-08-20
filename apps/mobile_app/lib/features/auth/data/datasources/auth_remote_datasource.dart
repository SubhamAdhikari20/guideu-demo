import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../models/auth_token_model.dart';
import '../models/auth_user_model.dart';

/// Talks to the core-engine auth endpoints over Dio.
class AuthRemoteDataSource {
  const AuthRemoteDataSource(this._dio);

  final Dio _dio;

  Future<AuthTokenModel> login({
    required String email,
    required String password,
  }) async {
    final resp = await _dio.post(
      ApiEndpoints.login,
      data: <String, dynamic>{'email': email, 'password': password},
    );
    return AuthTokenModel.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<void> register({
    required String username,
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    String? phoneNumber,
    required String role,
    String? licenseNumber,
    String? bio,
  }) async {
    await _dio.post(
      ApiEndpoints.register,
      data: <String, dynamic>{
        'username': username,
        'email': email,
        'password': password,
        'first_name': firstName,
        'last_name': lastName,
        'role': role,
        if (phoneNumber != null && phoneNumber.isNotEmpty) 'phone_number': phoneNumber,
        if (licenseNumber != null && licenseNumber.isNotEmpty) 'license_number': licenseNumber,
        if (bio != null && bio.isNotEmpty) 'bio': bio,
      },
    );
  }

  Future<AuthUserModel> currentUser() async {
    final resp = await _dio.get(ApiEndpoints.me);
    return AuthUserModel.fromJson(resp.data as Map<String, dynamic>);
  }
}
