import '../../domain/entities/price_check_result.dart';

/// Maps the `trust/price-check` JSON response to a [PriceCheckResult].
class PriceCheckResultModel {
  const PriceCheckResultModel(this._json);

  final Map<String, dynamic> _json;

  PriceCheckResult toEntity() {
    return PriceCheckResult(
      serviceType: (_json['service_type'] ?? '') as String,
      region: _json['region'] as String?,
      season: _json['season'] as String?,
      quotedPriceNpr: _toInt(_json['quoted_price_npr']),
      benchmarkPriceNpr:
          _json['benchmark_price_npr'] == null ? null : _toInt(_json['benchmark_price_npr']),
      overchargeRatio: _toDoubleOrNull(_json['overcharge_ratio']),
      isLikelyScam: (_json['is_likely_scam'] ?? false) as bool,
      severity: _json['severity'] as String?,
      scamProbability: _toDoubleOrNull(_json['scam_probability']),
      source: (_json['source'] ?? '') as String,
      explanation: _stringList(_json['explanation']),
      belowFairWage: (_json['below_fair_wage'] ?? false) as bool,
      belowFairRange: (_json['below_fair_range'] ?? false) as bool,
      fairWageMessage: _json['fair_wage_message'] as String?,
    );
  }

  static int _toInt(dynamic v) {
    if (v is int) return v;
    if (v is num) return v.round();
    if (v is String) return int.tryParse(v) ?? 0;
    return 0;
  }

  static double? _toDoubleOrNull(dynamic v) {
    if (v == null) return null;
    if (v is num) return v.toDouble();
    if (v is String) return double.tryParse(v);
    return null;
  }

  static List<String> _stringList(dynamic v) {
    if (v is List) return v.map((e) => e.toString()).toList();
    return const [];
  }
}
