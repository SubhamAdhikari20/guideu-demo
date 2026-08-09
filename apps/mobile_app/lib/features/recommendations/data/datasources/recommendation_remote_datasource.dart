import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../destinations/data/models/destination_model.dart';
import '../../../guides/data/models/guide_model.dart';

/// Reads the personalised feed from the core-engine, which in turn asks the
/// analytics-engine to rank routes / guides. The feed returns the same catalog
/// JSON the Explore and Guides screens already use (plus a score we ignore here),
/// so we reuse [DestinationModel] and [GuideModel] to parse it.
class RecommendationRemoteDataSource {
  const RecommendationRemoteDataSource(this._dio);

  final Dio _dio;

  /// Returns each route with the ranker's `why` lines still attached.
  Future<List<({DestinationModel route, List<String> why, double? score})>>
      getRecommendedRoutes() async {
    final resp = await _dio.get(ApiEndpoints.recommendRoutes);
    return _results(resp.data).map((e) {
      final json = e as Map<String, dynamic>;
      final why = json['why'];
      return (
        route: DestinationModel.fromJson(json),
        why: why is List ? why.map((w) => w.toString()).toList() : <String>[],
        score: (json['score'] as num?)?.toDouble(),
      );
    }).toList();
  }

  Future<List<GuideModel>> getRecommendedGuides() async {
    final resp = await _dio.get(ApiEndpoints.recommendGuides);
    return _results(resp.data)
        .map((e) => GuideModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// The feed wraps its list in `{source, model_version, results}`.
  List<dynamic> _results(dynamic data) {
    if (data is Map && data['results'] is List) {
      return data['results'] as List<dynamic>;
    }
    if (data is List) return data;
    return const [];
  }
}
