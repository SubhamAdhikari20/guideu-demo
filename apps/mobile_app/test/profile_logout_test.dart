import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:guideu_mobile/features/auth/domain/entities/auth_user.dart';
import 'package:guideu_mobile/features/auth/presentation/providers/auth_providers.dart';
import 'package:guideu_mobile/features/auth/presentation/providers/auth_state.dart';
import 'package:guideu_mobile/features/profile/presentation/pages/profile_page.dart';

class _TestAuthController extends AuthController {
  @override
  AuthState build() => const AuthAuthenticated(
    AuthUser(
      id: '1',
      email: 'tourist@guideu.local',
      fullName: 'Asha Gurung',
      role: 'TOURIST',
    ),
  );

  @override
  Future<void> logout() async {
    state = const AuthUnauthenticated();
  }
}

void main() {
  testWidgets('logging out leaves the protected shell and opens login', (
    tester,
  ) async {
    final router = GoRouter(
      initialLocation: '/profile',
      routes: [
        GoRoute(
          path: '/profile',
          builder: (context, state) => const ProfilePage(),
        ),
        GoRoute(
          path: '/login',
          builder: (context, state) =>
              const Scaffold(body: Text('Login destination')),
        ),
      ],
    );
    addTearDown(router.dispose);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_TestAuthController.new),
        ],
        child: MaterialApp.router(routerConfig: router),
      ),
    );

    await tester.drag(find.byType(ListView), const Offset(0, -1200));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Log out'));
    await tester.pumpAndSettle();

    expect(find.text('Login destination'), findsOneWidget);
    expect(router.routeInformationProvider.value.uri.path, '/login');
  });
}
