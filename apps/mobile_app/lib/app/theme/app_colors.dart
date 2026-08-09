import 'package:flutter/material.dart';

/// GuideU brand palette — teal wordmark with a gold call-to-action, taken from
/// the logo and the prototype designs.
class AppColors {
  AppColors._();

  static const Color primary = Color(0xFF138086); // GuideU teal
  static const Color primaryDark = Color(0xFF0C5F63);
  static const Color gold = Color(0xFFF5B400); // CTA / accent
  static const Color background = Color(0xFFFFFFFF);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color inputFill = Color(0xFFF1EFEE); // light grey input fields
  static const Color textPrimary = Color(0xFF1B1B1B);
  static const Color textSecondary = Color(0xFF8A8A8A);
  static const Color border = Color(0xFFE3E0DE);
  static const Color error = Color(0xFFE2231A);
  static const Color success = Color(0xFF2E9E5B);
  // Used where something needs attention but is not a failure — e.g. a quote
  // that falls below the fair wage for a guide or porter.
  static const Color warning = Color(0xFFB86E00);
}
