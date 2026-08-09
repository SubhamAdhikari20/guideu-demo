import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../auth/presentation/providers/auth_providers.dart';
import '../../../auth/presentation/providers/auth_state.dart';
import '../../../anti_scam/presentation/pages/price_check_page.dart';
import '../../../bookings/presentation/pages/packages_page.dart';
import '../../../chat/presentation/pages/chat_threads_page.dart';
import '../../../destinations/domain/entities/destination.dart';
import '../../../destinations/presentation/widgets/destination_detail_sheet.dart';
import '../../../guides/domain/entities/guide.dart';
import '../../../guides/presentation/providers/guide_providers.dart';
import '../../../guides/presentation/widgets/guide_profile_sheet.dart';
import '../../../recommendations/presentation/providers/recommendation_providers.dart';
import '../../../workspace/presentation/pages/workspaces_list_page.dart';

/// Home tab — discovery landing styled after the Home prototype: greeting,
/// search, a hero banner, quick actions and a "Nearby Guides" strip.
class HomePage extends ConsumerWidget {
  const HomePage({this.onSeeExplore, this.onSeeGuides, super.key});

  final VoidCallback? onSeeExplore;
  final VoidCallback? onSeeGuides;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(authControllerProvider);
    final name = state is AuthAuthenticated
        ? state.user.fullName.split(' ').first
        : 'traveller';
    final nearbyGuides = ref.watch(guidesProvider(''));
    final recommended = ref.watch(recommendedRoutesProvider);

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            _Header(name: name),
            const SizedBox(height: 16),
            _SearchBar(onTap: onSeeExplore),
            const SizedBox(height: 16),
            const _HeroBanner(),
            const SizedBox(height: 24),
            _RecommendedRoutes(
              recommended: recommended,
              onSeeAll: onSeeExplore,
              onTap: (route) => showDestinationDetailSheet(
                context,
                route,
                onFindGuide: onSeeGuides,
              ),
            ),
            const SizedBox(height: 20),
            _QuickActions(onGuides: onSeeGuides),
            const SizedBox(height: 20),
            _PackagesCta(
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const PackagesPage()),
              ),
            ),
            const SizedBox(height: 12),
            _PlanTripCta(
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const WorkspacesListPage()),
              ),
            ),
            const SizedBox(height: 12),
            _SafetyCta(
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const PriceCheckPage()),
              ),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                const Text(
                  'Nearby Guides',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                TextButton(
                  onPressed: onSeeGuides,
                  child: const Text('See all'),
                ),
              ],
            ),
            const SizedBox(height: 4),
            SizedBox(
              height: 150,
              child: nearbyGuides.when(
                loading: () =>
                    const Center(child: CircularProgressIndicator()),
                error: (_, _) => const Center(
                  child: Text(
                    'Could not load guides.',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                ),
                data: (guides) {
                  if (guides.isEmpty) {
                    return const Center(
                      child: Text(
                        'No guides yet.',
                        style: TextStyle(color: AppColors.textSecondary),
                      ),
                    );
                  }
                  final preview = guides.take(6).toList();
                  return ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: preview.length,
                    separatorBuilder: (_, _) => const SizedBox(width: 12),
                    itemBuilder: (context, i) => _NearbyGuideCard(
                      guide: preview[i],
                      onTap: () => showGuideProfileSheet(context, preview[i]),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.name});

  final String name;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Namaste, $name 👋',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 2),
            Row(
              children: const [
                Icon(Icons.location_on, size: 14, color: AppColors.primary),
                SizedBox(width: 2),
                Text(
                  'Kathmandu, Nepal',
                  style:
                      TextStyle(color: AppColors.textSecondary, fontSize: 13),
                ),
              ],
            ),
          ],
        ),
        const Spacer(),
        IconButton(
          icon: const Icon(Icons.chat_bubble_outline),
          tooltip: 'Messages',
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const ChatThreadsPage()),
          ),
        ),
        IconButton(
          icon: const Icon(Icons.notifications_none),
          onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Notifications are coming soon.')),
          ),
        ),
      ],
    );
  }
}

class _SearchBar extends StatelessWidget {
  const _SearchBar({this.onTap});

  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: AppColors.inputFill,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          children: const [
            Icon(Icons.search, color: AppColors.textSecondary),
            SizedBox(width: 10),
            Text(
              'Explore destinations',
              style: TextStyle(color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}

class _HeroBanner extends StatelessWidget {
  const _HeroBanner();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 150,
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.primary, AppColors.primaryDark],
        ),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: const [
          Text(
            'Discover Nepal',
            style: TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 4),
          Text(
            'Experience the beauty of the Himalayas',
            style: TextStyle(color: Colors.white70),
          ),
        ],
      ),
    );
  }
}

class _QuickActions extends StatelessWidget {
  const _QuickActions({this.onGuides});

  final VoidCallback? onGuides;

  @override
  Widget build(BuildContext context) {
    void soon(String label) => ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$label booking is coming soon.')),
        );

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        _ActionItem(
          icon: Icons.hiking,
          label: 'Guides',
          onTap: onGuides ?? () {},
        ),
        _ActionItem(
          icon: Icons.hotel,
          label: 'Hotels',
          onTap: () => soon('Hotel'),
        ),
        _ActionItem(
          icon: Icons.flight,
          label: 'Flights',
          onTap: () => soon('Flight'),
        ),
        _ActionItem(
          icon: Icons.directions_bus,
          label: 'Buses',
          onTap: () => soon('Bus'),
        ),
      ],
    );
  }
}

class _ActionItem extends StatelessWidget {
  const _ActionItem({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Column(
        children: [
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(icon, color: AppColors.primary, size: 28),
          ),
          const SizedBox(height: 6),
          Text(label, style: const TextStyle(fontSize: 13)),
        ],
      ),
    );
  }
}

class _PackagesCta extends StatelessWidget {
  const _PackagesCta({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.gold.withValues(alpha: 0.14),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          children: [
            const Icon(Icons.card_travel, color: AppColors.gold),
            const SizedBox(width: 12),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Tour Packages',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                  ),
                  SizedBox(height: 2),
                  Text(
                    'Book curated treks and tours across Nepal',
                    style:
                        TextStyle(color: AppColors.textSecondary, fontSize: 12.5),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AppColors.textSecondary),
          ],
        ),
      ),
    );
  }
}

class _PlanTripCta extends StatelessWidget {
  const _PlanTripCta({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.gold.withValues(alpha: 0.14),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          children: const [
            Icon(Icons.map_outlined, color: AppColors.gold),
            SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Plan your trip',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                  SizedBox(height: 2),
                  Text(
                    'Build a day-by-day itinerary with a budget tracker',
                    style: TextStyle(color: AppColors.textSecondary, fontSize: 12.5),
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_right, color: AppColors.textSecondary),
          ],
        ),
      ),
    );
  }
}

class _SafetyCta extends StatelessWidget {
  const _SafetyCta({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.primary.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.primary.withValues(alpha: 0.25)),
        ),
        child: Row(
          children: const [
            Icon(Icons.shield_outlined, color: AppColors.primary),
            SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Is this price fair?',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                  ),
                  SizedBox(height: 2),
                  Text(
                    'Check a quoted price and avoid getting overcharged',
                    style:
                        TextStyle(color: AppColors.textSecondary, fontSize: 12.5),
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_right, color: AppColors.textSecondary),
          ],
        ),
      ),
    );
  }
}

class _RecommendedRoutes extends StatelessWidget {
  const _RecommendedRoutes({
    required this.recommended,
    required this.onTap,
    this.onSeeAll,
  });

  final AsyncValue<List<Destination>> recommended;
  final void Function(Destination route) onTap;
  final VoidCallback? onSeeAll;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.auto_awesome, size: 18, color: AppColors.gold),
            const SizedBox(width: 6),
            const Text(
              'Recommended for you',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const Spacer(),
            TextButton(onPressed: onSeeAll, child: const Text('See all')),
          ],
        ),
        const SizedBox(height: 4),
        SizedBox(
          height: 150,
          child: recommended.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (_, _) => const Center(
              child: Text(
                'Could not load recommendations.',
                style: TextStyle(color: AppColors.textSecondary),
              ),
            ),
            data: (routes) {
              if (routes.isEmpty) {
                return const Center(
                  child: Text(
                    'No suggestions yet.',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                );
              }
              final preview = routes.take(8).toList();
              return ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: preview.length,
                separatorBuilder: (_, _) => const SizedBox(width: 12),
                itemBuilder: (context, i) => _RecommendedRouteCard(
                  route: preview[i],
                  onTap: () => onTap(preview[i]),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _RecommendedRouteCard extends StatelessWidget {
  const _RecommendedRouteCard({required this.route, required this.onTap});

  final Destination route;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 200,
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 64,
              width: double.infinity,
              decoration: const BoxDecoration(
                borderRadius: BorderRadius.vertical(top: Radius.circular(13)),
                gradient: LinearGradient(
                  colors: [AppColors.primary, AppColors.primaryDark],
                ),
              ),
              child: const Align(
                alignment: Alignment.topRight,
                child: Padding(
                  padding: EdgeInsets.all(8),
                  child: Icon(Icons.terrain, color: Colors.white70, size: 20),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    route.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    route.region,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      const Icon(Icons.schedule,
                          size: 13, color: AppColors.textSecondary),
                      const SizedBox(width: 3),
                      Text(
                        route.durationLabel,
                        style: const TextStyle(fontSize: 12),
                      ),
                      const Spacer(),
                      Text(
                        route.difficulty,
                        style: const TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w600,
                          color: AppColors.primary,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NearbyGuideCard extends StatelessWidget {
  const _NearbyGuideCard({required this.guide, required this.onTap});

  final Guide guide;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 160,
        padding: const EdgeInsets.all(12),
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
                Container(
                  width: 40,
                  height: 40,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(
                      colors: [AppColors.primary, AppColors.primaryDark],
                    ),
                  ),
                  child: const Icon(Icons.person, color: Colors.white, size: 22),
                ),
                const Spacer(),
                if (guide.isVerified)
                  const Icon(Icons.verified,
                      size: 16, color: AppColors.primary),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              guide.guideCode,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 2),
            Text(
              guide.certification,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12,
              ),
            ),
            const Spacer(),
            Row(
              children: [
                const Icon(Icons.star, size: 14, color: AppColors.gold),
                const SizedBox(width: 3),
                Text(
                  guide.ratingLabel,
                  style: const TextStyle(
                    fontSize: 12.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
