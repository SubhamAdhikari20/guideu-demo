import 'package:flutter/material.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../chat/presentation/pages/chat_threads_page.dart';
import '../../../guide_requests/presentation/pages/guide_requests_page.dart';
import '../../../profile/presentation/pages/profile_page.dart';
import 'guide_dashboard_page.dart';

class GuideShellPage extends StatefulWidget {
  const GuideShellPage({super.key});
  @override
  State<GuideShellPage> createState() => _GuideShellPageState();
}

class _GuideShellPageState extends State<GuideShellPage> {
  int _index = 0;
  @override
  Widget build(BuildContext context) {
    const pages = [
      GuideDashboardPage(),
      GuideRequestsPage(guideMode: true),
      GuideRequestsPage(guideMode: true, assignmentsOnly: true),
      ChatThreadsPage(),
      ProfilePage(),
    ];
    return Scaffold(
      body: IndexedStack(index: _index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        indicatorColor: AppColors.primary.withValues(alpha: .12),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard, color: AppColors.primary), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.radar_outlined), selectedIcon: Icon(Icons.radar, color: AppColors.primary), label: 'Requests'),
          NavigationDestination(icon: Icon(Icons.assignment_outlined), selectedIcon: Icon(Icons.assignment, color: AppColors.primary), label: 'Trips'),
          NavigationDestination(icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble, color: AppColors.primary), label: 'Chat'),
          NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person, color: AppColors.primary), label: 'Profile'),
        ],
      ),
    );
  }
}
