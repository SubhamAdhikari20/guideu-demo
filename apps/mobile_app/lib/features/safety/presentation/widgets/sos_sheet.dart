import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/theme/app_colors.dart';
import '../providers/sos_providers.dart';

/// Shows the emergency SOS confirmation sheet.
Future<void> showSosSheet(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.surface,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) => const _SosSheet(),
  );
}

class _SosSheet extends ConsumerStatefulWidget {
  const _SosSheet();

  @override
  ConsumerState<_SosSheet> createState() => _SosSheetState();
}

class _SosSheetState extends ConsumerState<_SosSheet> {
  final _message = TextEditingController();
  bool _sending = false;

  @override
  void dispose() {
    _message.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    setState(() => _sending = true);
    try {
      await ref.read(sosRemoteDataSourceProvider).sendSos(message: _message.text.trim());
      if (!mounted) return;
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('SOS sent. Help has been alerted — stay where you are if safe.'),
          backgroundColor: AppColors.error,
        ),
      );
    } catch (_) {
      if (!mounted) return;
      setState(() => _sending = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not send the SOS. Please try again.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16, right: 16, top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.sos, color: AppColors.error),
              SizedBox(width: 8),
              Text('Emergency SOS',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'This raises an emergency alert on your account so responders can reach you. '
            'Only use it in a real emergency.',
            style: TextStyle(color: AppColors.textSecondary),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _message,
            maxLines: 2,
            decoration: const InputDecoration(
              labelText: 'What is happening? (optional)',
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              style: FilledButton.styleFrom(backgroundColor: AppColors.error),
              onPressed: _sending ? null : _send,
              icon: const Icon(Icons.warning_amber_rounded),
              label: Text(_sending ? 'Sending...' : 'Send SOS now'),
            ),
          ),
        ],
      ),
    );
  }
}
