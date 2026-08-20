import '../../../../core/error/failures.dart';
import '../entities/auth_user.dart';

/// Auth contract the presentation layer depends on. The data layer implements
/// it. Returns a `(Failure?, AuthUser?)` record — exactly one side is non-null.
abstract interface class AuthRepository {
  Future<(Failure?, AuthUser?)> login({
    required String email,
    required String password,
  });

  Future<(Failure?, AuthUser?)> register({
    required String fullName,
    required String email,
    required String password,
    String? phoneNumber,
    required String role,
    String? licenseNumber,
    String? bio,
  });

  Future<(Failure?, AuthUser?)> currentUser();

  Future<void> logout();
}
