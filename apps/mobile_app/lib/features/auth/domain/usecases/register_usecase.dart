import '../../../../core/error/failures.dart';
import '../entities/auth_user.dart';
import '../repositories/auth_repository.dart';

class RegisterParams {
  const RegisterParams({
    required this.fullName,
    required this.email,
    required this.password,
    this.phoneNumber,
    this.role = 'TOURIST',
    this.licenseNumber,
    this.bio,
  });
  final String fullName;
  final String email;
  final String password;
  final String? phoneNumber;
  final String role;
  final String? licenseNumber;
  final String? bio;
}

class RegisterUseCase {
  const RegisterUseCase(this._repository);
  final AuthRepository _repository;

  Future<(Failure?, AuthUser?)> call(RegisterParams params) => _repository.register(
        fullName: params.fullName,
        email: params.email,
        password: params.password,
        phoneNumber: params.phoneNumber,
        role: params.role,
        licenseNumber: params.licenseNumber,
        bio: params.bio,
      );
}
