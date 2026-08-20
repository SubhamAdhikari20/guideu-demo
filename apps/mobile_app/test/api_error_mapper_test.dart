// A wrong password on the login screen showed the user this, verbatim:
//
//   {type: validation, detail: {non_field_errors: [Invalid email or password.]},
//    status: 400}
//
// The core-engine wraps errors in an {"error": {...}} envelope. None of the
// eleven per-feature mappers knew about it, so they fell through to printing the
// raw inner map instead of the sentence the server had already written.
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:guideu_mobile/core/error/api_error_mapper.dart';
import 'package:guideu_mobile/core/error/failures.dart';

DioException _http(int status, dynamic body) => DioException(
      requestOptions: RequestOptions(path: '/auth/token/'),
      type: DioExceptionType.badResponse,
      response: Response<dynamic>(
        requestOptions: RequestOptions(path: '/auth/token/'),
        statusCode: status,
        data: body,
      ),
    );

void main() {
  group('core-engine error envelope', () {
    test('a wrong password reads as a sentence, not a map dump', () {
      final failure = mapDioError(_http(400, {
        'error': {
          'type': 'validation',
          'detail': {
            'non_field_errors': ['Invalid email or password.'],
          },
          'status': 400,
        },
      }));

      expect(failure, isA<ServerFailure>());
      expect(failure.message, 'Invalid email or password.');
      expect(failure.message, isNot(contains('non_field_errors')));
      expect(failure.message, isNot(contains('{')));
    });

    test("a field error surfaces that field's message", () {
      final failure = mapDioError(_http(400, {
        'error': {
          'type': 'validation',
          'detail': {
            'email': ['Enter a valid email address.'],
          },
          'status': 400,
        },
      }));
      expect(failure.message, 'Enter a valid email address.');
    });

    test('an auth failure surfaces its detail string', () {
      final failure = mapDioError(_http(401, {
        'error': {
          'type': 'notauthenticated',
          'detail': {'detail': 'Authentication credentials were not provided.'},
          'status': 401,
        },
      }));
      expect(failure.message, 'Authentication credentials were not provided.');
      expect((failure as ServerFailure).statusCode, 401);
    });

    test('non_field_errors wins over a field error', () {
      final failure = mapDioError(_http(400, {
        'error': {
          'detail': {
            'email': ['Some field note.'],
            'non_field_errors': ['The form-level message.'],
          },
        },
      }));
      expect(failure.message, 'The form-level message.');
    });
  });

  group('bare DRF bodies still work', () {
    test('top-level detail', () {
      expect(mapDioError(_http(403, {'detail': 'Not allowed.'})).message, 'Not allowed.');
    });
    test('top-level field errors', () {
      expect(
        mapDioError(_http(400, {'quoted_price_npr': ['Must be positive.']})).message,
        'Must be positive.',
      );
    });
  });

  group('fallbacks', () {
    test('connection problems become a NetworkFailure', () {
      for (final type in [
        DioExceptionType.connectionError,
        DioExceptionType.connectionTimeout,
        DioExceptionType.receiveTimeout,
        DioExceptionType.sendTimeout,
      ]) {
        final failure = mapDioError(DioException(
          requestOptions: RequestOptions(path: '/x'),
          type: type,
        ));
        expect(failure, isA<NetworkFailure>(), reason: '$type');
        expect(failure.message, 'No internet connection');
      }
    });

    test("an unreadable body uses the caller's fallback", () {
      final failure = mapDioError(_http(500, null), fallback: 'Could not load festivals.');
      expect(failure.message, 'Could not load festivals.');
    });

    test('an empty map uses the fallback rather than "{}"', () {
      expect(mapDioError(_http(500, <String, dynamic>{})).message,
          'Something went wrong. Please try again.');
    });
  });
}
