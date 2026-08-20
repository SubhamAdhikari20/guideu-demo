import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Branded text field used across the auth screens (filled grey, rounded).
///
/// Email fields get extra care. On Android the soft keyboard will happily
/// autocorrect, auto-capitalise, and insert a space after a full stop (the
/// double-space-to-period shortcut) — so "tourist@guideu.local" arrives as
/// "tourist@guideu. local". `trim()` does not help, because the space is in the
/// middle, and the form then rejects a login the user typed correctly. Since an
/// email address can never contain whitespace, the simplest fix is to refuse to
/// accept it in the first place rather than validate it after the fact.
class AuthTextField extends StatelessWidget {
  const AuthTextField({
    super.key,
    required this.controller,
    required this.hint,
    this.keyboardType,
    this.obscureText = false,
    this.validator,
    this.textInputAction,
  });

  final TextEditingController controller;
  final String hint;
  final TextInputType? keyboardType;
  final bool obscureText;
  final String? Function(String?)? validator;
  final TextInputAction? textInputAction;

  bool get _isEmail => keyboardType == TextInputType.emailAddress;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      obscureText: obscureText,
      validator: validator,
      textInputAction: textInputAction,
      // Suggestions and autocorrect are wrong for both emails and passwords:
      // one gets mangled, the other gets leaked into the keyboard's dictionary.
      autocorrect: false,
      enableSuggestions: !_isEmail && !obscureText,
      // A password field must never transform what was typed — auto-capitalising
      // the first character silently changes the credential, and the only
      // feedback is "invalid email or password". Sentence case is only right for
      // free text such as a name.
      textCapitalization: _isEmail || obscureText
          ? TextCapitalization.none
          : TextCapitalization.sentences,
      autofillHints: _isEmail ? const [AutofillHints.email] : null,
      inputFormatters: _isEmail
          ? [FilteringTextInputFormatter.deny(RegExp(r'\s'))]
          : null,
      decoration: InputDecoration(hintText: hint),
    );
  }
}
