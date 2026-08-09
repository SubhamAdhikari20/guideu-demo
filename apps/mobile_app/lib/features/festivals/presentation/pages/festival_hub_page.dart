import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/theme/app_colors.dart';
import '../../domain/entities/festival.dart';
import '../providers/festival_providers.dart';

/// Information hub — a calendar of Nepal's festivals over the coming year, so
/// travellers can plan around Dashain, Tihar, Holi and the rest.
class FestivalHubPage extends ConsumerWidget {
  const FestivalHubPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final festivals = ref.watch(upcomingFestivalsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Festivals & Events')),
      body: festivals.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.celebration_outlined,
                    size: 48, color: AppColors.textSecondary),
                const SizedBox(height: 12),
                const Text(
                  'Could not load the festival calendar.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppColors.textSecondary),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () => ref.invalidate(upcomingFestivalsProvider),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (months) {
          final withFestivals =
              months.where((m) => m.festivals.isNotEmpty).toList();
          if (withFestivals.isEmpty) {
            return const Center(
              child: Text(
                'No festivals found. Seed the catalog to see the calendar.',
                style: TextStyle(color: AppColors.textSecondary),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(upcomingFestivalsProvider),
            child: ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
              itemCount: withFestivals.length,
              itemBuilder: (context, i) => _MonthSection(month: withFestivals[i]),
            ),
          );
        },
      ),
    );
  }
}

class _MonthSection extends StatelessWidget {
  const _MonthSection({required this.month});

  final FestivalMonth month;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Row(
            children: [
              const Icon(Icons.calendar_month, size: 18, color: AppColors.primary),
              const SizedBox(width: 6),
              Text(
                month.monthName,
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ],
          ),
        ),
        for (final f in month.festivals) _FestivalCard(festival: f),
        const SizedBox(height: 8),
      ],
    );
  }
}

class _FestivalCard extends StatelessWidget {
  const _FestivalCard({required this.festival});

  final Festival festival;

  Color get _typeColor {
    switch (festival.type) {
      case 'Religious':
        return AppColors.primary;
      case 'Seasonal':
        return AppColors.success;
      default:
        return AppColors.gold;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  festival.name,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _typeColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  festival.type,
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w600,
                    color: _typeColor,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(Icons.schedule, size: 14, color: AppColors.textSecondary),
              const SizedBox(width: 4),
              Text(festival.durationLabel,
                  style: const TextStyle(fontSize: 12.5)),
              const SizedBox(width: 14),
              const Icon(Icons.place_outlined,
                  size: 14, color: AppColors.textSecondary),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  festival.regionLabel,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 12.5),
                ),
              ),
            ],
          ),
          if (festival.badgeEligible) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.workspace_premium, size: 14, color: AppColors.gold),
                const SizedBox(width: 4),
                Text(
                  'Earn ${festival.badgePoints} points if you join',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
