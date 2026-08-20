/// Simple, reusable form validators used across the auth screens.
class Validators {
  Validators._();

  static final RegExp _emailPattern = RegExp(r'^[\w.\-+]+@[\w\-]+(\.[\w\-]+)+$');

  /// Strip every whitespace character, not just the ends.
  ///
  /// An email address cannot contain whitespace, so anything we find is an
  /// artefact of how it was entered — a keyboard autocorrect, or a newline that
  /// came along with a paste. `trim()` only handles the ends, which let
  /// "tourist@guideu. local" through to a rejection the user could not explain.
  static String normaliseEmail(String? value) =>
      (value ?? '').replaceAll(RegExp(r'\s'), '');

  /// Validate an email, saying *why* it failed rather than only that it did.
  static String? email(String? value) {
    if (value == null || value.trim().isEmpty) return 'Email is required';

    final cleaned = normaliseEmail(value);
    if (!cleaned.contains('@')) return 'Email must contain an @';
    if (cleaned.split('@').length > 2) return 'Email has more than one @';

    final domain = cleaned.split('@').last;
    if (domain.isEmpty) return 'Add the part after the @, e.g. guideu.local';
    if (!domain.contains('.')) return 'Domain needs a dot, e.g. guideu.local';

    return _emailPattern.hasMatch(cleaned) ? null : 'Enter a valid email';
  }

  static String? password(String? value) {
    if (value == null || value.isEmpty) return 'Password is required';
    return value.length >= 8 ? null : 'Password must be at least 8 characters';
  }

  static String? required(String? value, String field) {
    return (value == null || value.trim().isEmpty) ? '$field is required' : null;
  }
}
