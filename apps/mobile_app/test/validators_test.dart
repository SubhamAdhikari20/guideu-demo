// Login rejected the seeded demo accounts with "Enter a valid email" even when
// the address was typed correctly. The cause was not the pattern: Android's
// keyboard inserts a space after a full stop (the double-space-to-period
// shortcut), so "tourist@guideu.local" reached the form as
// "tourist@guideu. local". `trim()` cannot help — the space is in the middle.
import 'package:flutter_test/flutter_test.dart';
import 'package:guideu_mobile/core/utils/validators.dart';

void main() {
  group('Validators.email accepts the seeded demo accounts', () {
    for (final email in const [
      'tourist@guideu.local',
      'guide@guideu.local',
      'admin@guideu.local',
      'demo_tourist_0@example.com',
    ]) {
      test(email, () => expect(Validators.email(email), isNull));
    }
  });

  group('whitespace the keyboard injects is normalised away', () {
    for (final entry in const {
      'tourist@guideu. local': 'space after the dot',
      'tourist @guideu.local': 'space before the @',
      'tourist@ guideu.local': 'space after the @',
      ' tourist@guideu.local ': 'padding from a paste',
      'tourist@guideu.local\n': 'newline from a paste',
    }.entries) {
      test(entry.value, () {
        expect(Validators.email(entry.key), isNull);
        expect(
          Validators.normaliseEmail(entry.key),
          'tourist@guideu.local',
          reason: 'the value sent to the API must be the clean address',
        );
      });
    }
  });

  group('genuinely invalid input still fails, and says why', () {
    test('empty', () => expect(Validators.email(''), 'Email is required'));
    test('no @', () => expect(Validators.email('tourist.guideu.local'),
        'Email must contain an @'));
    test('two @', () => expect(Validators.email('a@b@guideu.local'),
        'Email has more than one @'));
    test('nothing after @', () => expect(Validators.email('tourist@'),
        'Add the part after the @, e.g. guideu.local'));
    test('domain without a dot', () => expect(Validators.email('tourist@guideu'),
        'Domain needs a dot, e.g. guideu.local'));
  });

  group('password', () {
    test('required', () => expect(Validators.password(''), 'Password is required'));
    test('too short', () => expect(Validators.password('1234567'),
        'Password must be at least 8 characters'));
    test('accepts the demo passwords', () {
      expect(Validators.password('TouristDemo123!'), isNull);
      expect(Validators.password('GuideDemo123!'), isNull);
    });
  });
}
