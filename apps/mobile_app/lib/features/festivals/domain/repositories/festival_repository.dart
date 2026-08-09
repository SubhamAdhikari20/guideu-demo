import '../../../../core/error/failures.dart';
import '../entities/festival.dart';

abstract interface class FestivalRepository {
  Future<(Failure?, List<FestivalMonth>?)> getUpcoming({int months});
}
