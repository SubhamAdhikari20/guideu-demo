import 'package:flutter/material.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../destinations/presentation/pages/explore_page.dart';
import '../../../festivals/presentation/pages/festival_hub_page.dart';
import '../../../guides/presentation/pages/guides_page.dart';
import '../../../profile/presentation/pages/profile_page.dart';
import 'home_page.dart';

/// The signed-in shell: a bottom navigation bar over the Home, Explore, Guides
/// and Profile tabs. Tabs keep their state via an [IndexedStack].
class MainShellPage extends StatefulWidget {
  const MainShellPage({super.key});

  @override
  State<MainShellPage> createState() => _MainShellPageState();
}

class _MainShellPageState extends State<MainShellPage> {
  int _index = 0;

  void _goTo(int index) => setState(() => _index = index);

  @override
  Widget build(BuildContext context) {
    final pages = [
      HomePage(
        onSeeExplore: () => _goTo(1),
        onSeeGuides: () => _goTo(2),
      ),
      ExplorePage(onFindGuide: () => _goTo(2)),
      const GuidesPage(),
      const FestivalHubPage(),
      const ProfilePage(),
    ];

    return Scaffold(
      body: IndexedStack(index: _index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: _goTo,
        indicatorColor: AppColors.primary.withValues(alpha: 0.12),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home, color: AppColors.primary),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.explore_outlined),
            selectedIcon: Icon(Icons.explore, color: AppColors.primary),
            label: 'Explore',
          ),
          NavigationDestination(
            icon: Icon(Icons.hiking_outlined),
            selectedIcon: Icon(Icons.hiking, color: AppColors.primary),
            label: 'Guides',
          ),
          NavigationDestination(
            icon: Icon(Icons.celebration_outlined),
            selectedIcon: Icon(Icons.celebration, color: AppColors.primary),
            label: 'Festivals',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person, color: AppColors.primary),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}
