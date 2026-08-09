import '../../../../core/error/failures.dart';
import '../entities/price_check_result.dart';

/// Anti-scam tools: fair-price check and overcharge reporting.
abstract interface class AntiScamRepository {
  Future<(Failure?, PriceCheckResult?)> checkPrice({
    required String serviceType,
    required int quotedPriceNpr,
    String? region,
    String? season,
  });

  Future<(Failure?, bool?)> reportScam({
    required String serviceType,
    required String region,
    required int quotedPriceNpr,
    String? season,
    String description,
  });

  Future<(Failure?, List<String>?)> getRegionNames();
}
