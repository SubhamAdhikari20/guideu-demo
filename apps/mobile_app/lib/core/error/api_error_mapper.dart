import 'package:dio/dio.dart';

import 'failures.dart';

/// Turns a [DioException] into a [Failure] carrying a message fit to show a user.
///
/// The core-engine wraps every error in an envelope:
///
/// ```json
/// {"error": {"type": "validation",
///            "detail": {"non_field_errors": ["Invalid email or password."]},
///            "status": 400}}
/// ```
///
/// Each feature used to unwrap that itself, and none of them knew about the
/// envelope — they looked for `detail` or `non_field_errors` at the *top* level,
/// found neither, fell through to `data.values.first.toString()` and printed the
/// raw inner map. A wrong password therefore showed the user:
///
/// ```
/// {type: validation, detail: {non_field_errors: [Invalid email or password.]}, status: 400}
/// ```
///
/// when the server had sent a perfectly good sentence. Unwrapping lives here now
/// so all eleven repositories share one correct implementation.
Failure mapDioError(
  DioException e, {
  String fallback = 'Something went wrong. Please try again.',
}) {
  switch (e.type) {
    case DioExceptionType.connectionError:
    case DioExceptionType.connectionTimeout:
    case DioExceptionType.receiveTimeout:
    case DioExceptionType.sendTimeout:
      return const NetworkFailure();
    default:
      break;
  }

  final status = e.response?.statusCode;
  final message = _messageFrom(e.response?.data) ?? fallback;
  return ServerFailure(message, statusCode: status);
}

/// Dig the first human-readable sentence out of an error body, or null.
String? _messageFrom(dynamic data) {
  if (data is String && data.trim().isNotEmpty) return data.trim();
  if (data is! Map) return null;

  // Unwrap the core-engine envelope, then treat what is inside the same way as
  // a bare DRF body — the two shapes are otherwise identical.
  final inner = data['error'];
  if (inner is Map) {
    return _messageFrom(inner['detail']) ?? _messageFrom(inner['message']);
  }

  // DRF's own shapes: {"detail": "..."} or {"field": ["...", ...]}.
  final detail = data['detail'];
  if (detail is String && detail.trim().isNotEmpty) return detail.trim();

  // Prefer non_field_errors — it is the form-level message, which is almost
  // always the one worth showing.
  final nonField = _firstOf(data['non_field_errors']);
  if (nonField != null) return nonField;

  for (final value in data.values) {
    final candidate = _firstOf(value) ?? _messageFrom(value);
    if (candidate != null) return candidate;
  }
  return null;
}

/// First entry of a list of strings, if that is what this is.
String? _firstOf(dynamic value) {
  if (value is List && value.isNotEmpty) {
    final first = value.first;
    if (first is String && first.trim().isNotEmpty) return first.trim();
  }
  if (value is String && value.trim().isNotEmpty) return value.trim();
  return null;
}
