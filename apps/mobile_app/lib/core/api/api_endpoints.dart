/// Central registry of backend endpoints.
///
/// The base URL is compile-time configurable via `--dart-define`; the default
/// targets the Android emulator's host alias for a locally running core-engine.
class ApiEndpoints {
  ApiEndpoints._();

  static const String baseUrl = String.fromEnvironment(
    'GUIDEU_API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );

  /// Socket.IO base for the real-time-engine (live chat, presence).
  static const String realtimeBaseUrl = String.fromEnvironment(
    'GUIDEU_REALTIME_URL',
    defaultValue: 'http://10.0.2.2:8002',
  );

  static const Duration connectTimeout = Duration(seconds: 20);
  static const Duration receiveTimeout = Duration(seconds: 20);

  // Auth (core-engine)
  static const String login = '/auth/token/';
  static const String refresh = '/auth/token/refresh/';
  static const String register = '/auth/register/';
  static const String me = '/auth/users/me/';

  // Catalog (core-engine)
  static const String routes = '/catalog/routes/';
  static const String regions = '/catalog/regions/';
  static const String guidesRegistry = '/catalog/guides-registry/';
  static const String events = '/catalog/events/';
  static const String eventsUpcoming = '/catalog/events/upcoming/';
  static const String pricingLookup = '/catalog/pricing-benchmarks/lookup/';

  // Bookings (core-engine)
  static const String packages = '/bookings/packages/';
  static const String bookings = '/bookings/bookings/';

  // Payments (core-engine)
  static const String payments = '/payments/payments/';

  // Reviews (core-engine)
  static const String reviews = '/reviews/reviews/';
  static const String reviewSummary = '/reviews/reviews/summary/';

  // Recommendations (core-engine -> analytics-engine)
  static const String recommendRoutes = '/recommendations/routes/';
  static const String recommendGuides = '/recommendations/guides/';

  // Chat history (core-engine; live delivery via real-time-engine socket)
  static const String chatThreads = '/chat/threads/';
  static const String chatMessages = '/chat/messages/';

  // Trust / anti-scam (core-engine)
  static const String priceCheck = '/trust/price-check/';
  static const String scamReports = '/trust/scam-reports/';

  // Travel workspace (core-engine)
  static const String workspaceTrips = '/workspace/trips/';
  static const String workspaceItems = '/workspace/items/';
  static const String workspaceItemsReorder = '/workspace/items/reorder/';
  static String workspaceAiSuggestions(int tripId) =>
      '/workspace/trips/$tripId/ai-suggestions/';
  static String workspaceApplySuggestions(int tripId) =>
      '/workspace/trips/$tripId/apply-suggestions/';
  static String workspaceBudgetSummary(int tripId) =>
      '/workspace/trips/$tripId/budget-summary/';

  // Currency (core-engine)
  static const String currencyRates = '/currency/rates/';
  static const String currencyConvert = '/currency/convert/';

  // Safety SOS (core-engine)
  static const String sosAlerts = '/safety/sos/';
}
