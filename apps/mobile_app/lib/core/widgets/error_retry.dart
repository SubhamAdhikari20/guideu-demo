import 'package:flutter/material.dart';

import '../../app/theme/app_colors.dart';

/// A reusable error state with a retry button. Shows a friendly message — never
/// a raw exception — so failures look the same across the app.
class ErrorRetry extends StatelessWidget {
  const ErrorRetry({
    required this.onRetry,
    this.message = 'Something went wrong. Please try again.',
    super.key,
  });

  final VoidCallback onRetry;
  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off, size: 48, color: AppColors.textSecondary),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}
