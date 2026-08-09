import '../../../destinations/domain/entities/destination.dart';

/// A recommended trek together with the reasons the ranker put it there.
///
/// Ranking a list is choice architecture: whatever sits at the top changes what
/// people book. GuideU therefore carries the model's own reasoning through to
/// the screen instead of presenting an unexplained order, so a traveller can
/// see "why am I seeing this?" and disagree with it.
class RecommendedRoute {
  const RecommendedRoute({
    required this.destination,
    this.why = const [],
    this.score,
  });

  final Destination destination;

  /// Plain-language reasons, derived from the ranker's feature contributions.
  final List<String> why;

  final double? score;

  /// The single strongest reason, for the compact card on the Home screen.
  String? get topReason => why.isEmpty ? null : why.first;
}
