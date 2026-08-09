import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../auth/presentation/providers/auth_providers.dart';
import '../../../auth/presentation/providers/auth_state.dart';
import '../../../bookings/presentation/pages/my_bookings_page.dart';
import '../../../currency/presentation/pages/currency_converter_page.dart';
import '../../../safety/presentation/widgets/sos_sheet.dart';
import '../../../workspace/presentation/pages/workspaces_list_page.dart';

/// Profile tab — shows the signed-in user and lets them log out.
class ProfilePage extends ConsumerWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(authControllerProvider);
    final user = state is AuthAuthenticated ? state.user : null;

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          Center(
            child: Column(
              children: [
                Container(
                  width: 90,
                  height: 90,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [AppColors.primary, AppColors.primaryDark],
                    ),
                  ),
                  child: const Icon(Icons.person, color: Colors.white, size: 46),
                ),
                const SizedBox(height: 12),
                Text(
                  user?.fullName ?? 'Traveller',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  user?.email ?? '',
                  style: const TextStyle(color: AppColors.textSecondary),
                ),
                if (user != null) ...[
                  const SizedBox(height: 8),
                  _RoleBadge(role: user.role),
                ],
              ],
            ),
          ),
          const SizedBox(height: 24),
          _Tile(
            icon: Icons.receipt_long_outlined,
            label: 'My Bookings',
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const MyBookingsPage()),
            ),
          ),
          _Tile(
            icon: Icons.map_outlined,
            label: 'My Trips',
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const WorkspacesListPage()),
            ),
          ),
          _Tile(
            icon: Icons.currency_exchange,
            label: 'Currency Converter',
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const CurrencyConverterPage()),
            ),
          ),
          const _Tile(icon: Icons.settings_outlined, label: 'Settings'),
          const _Tile(icon: Icons.lock_outline, label: 'Security'),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: () => showSosSheet(context),
            icon: const Icon(Icons.sos, color: AppColors.error),
            label: const Text('Emergency SOS', style: TextStyle(color: AppColors.error)),
            style: OutlinedButton.styleFrom(side: const BorderSide(color: AppColors.error)),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
            icon: const Icon(Icons.logout, color: AppColors.error),
            label: const Text(
              'Log out',
              style: TextStyle(color: AppColors.error),
            ),
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: AppColors.error),
            ),
          ),
        ],
      ),
    );
  }
}

class _RoleBadge extends StatelessWidget {
  const _RoleBadge({required this.role});

  final String role;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.primary.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Text(
        role,
        style: const TextStyle(
          color: AppColors.primaryDark,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _Tile extends StatelessWidget {
  const _Tile({required this.icon, required this.label, this.onTap});

  final IconData icon;
  final String label;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(icon, color: AppColors.primary),
      title: Text(label),
      trailing: const Icon(Icons.chevron_right, color: AppColors.textSecondary),
      onTap: onTap ??
          () => ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('$label is coming soon.')),
              ),
    );
  }
}
