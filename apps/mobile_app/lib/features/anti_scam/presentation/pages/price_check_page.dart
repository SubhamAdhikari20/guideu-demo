import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/theme/app_colors.dart';
import '../../domain/entities/price_check_result.dart';
import '../providers/anti_scam_providers.dart';

/// "Is this price fair?" — the headline anti-scam tool. The tourist enters a
/// quoted price for a service and gets an explainable verdict from the backend
/// (ML-scored when available, else a benchmark rule). If it looks overpriced
/// they can report it in one tap.
class PriceCheckPage extends ConsumerStatefulWidget {
  const PriceCheckPage({super.key});

  @override
  ConsumerState<PriceCheckPage> createState() => _PriceCheckPageState();
}

const _serviceTypes = <String>[
  'Licensed Guide',
  'Porter',
  'Teahouse Lodge',
  'Hotel (Budget)',
  'Hotel (Mid-range)',
  'Hotel (Luxury)',
  'Meal (Trail)',
  'Meal (City)',
  'Taxi (Local)',
  'Tourist Bus',
  'Domestic Flight',
  'Jeep/4x4',
  'Rafting (Day)',
  'Paragliding (Tandem)',
];

const _seasons = <String>[
  'Peak (Autumn)',
  'Peak (Spring)',
  'Off (Monsoon)',
  'Off (Winter)',
];

class _PriceCheckPageState extends ConsumerState<PriceCheckPage> {
  final _formKey = GlobalKey<FormState>();
  final _priceController = TextEditingController();

  String _serviceType = _serviceTypes.first;
  String? _region;
  String? _season;
  PriceCheckQuery? _submitted;

  @override
  void dispose() {
    _priceController.dispose();
    super.dispose();
  }

  void _check() {
    if (!_formKey.currentState!.validate()) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _submitted = PriceCheckQuery(
        serviceType: _serviceType,
        quotedPriceNpr: int.parse(_priceController.text.trim()),
        region: _region,
        season: _season,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final regions = ref.watch(regionNamesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Is this price fair?')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Check a quoted price against the fair range for Nepal, so you '
                  'never get overcharged.',
                  style: TextStyle(color: AppColors.textSecondary),
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  initialValue: _serviceType,
                  decoration: const InputDecoration(labelText: 'Service'),
                  items: [
                    for (final s in _serviceTypes)
                      DropdownMenuItem(value: s, child: Text(s)),
                  ],
                  onChanged: (v) => setState(() => _serviceType = v ?? _serviceType),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _priceController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Quoted price (NPR)',
                    prefixText: 'Rs. ',
                  ),
                  validator: (v) {
                    final n = int.tryParse((v ?? '').trim());
                    if (n == null || n <= 0) return 'Enter a valid amount';
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                regions.when(
                  loading: () => const LinearProgressIndicator(),
                  error: (_, _) => const SizedBox.shrink(),
                  data: (names) => DropdownButtonFormField<String>(
                    initialValue: _region,
                    isExpanded: true,
                    decoration: const InputDecoration(labelText: 'Region (optional)'),
                    items: [
                      const DropdownMenuItem(value: null, child: Text('Any region')),
                      for (final n in names)
                        DropdownMenuItem(value: n, child: Text(n)),
                    ],
                    onChanged: (v) => setState(() => _region = v),
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: _season,
                  decoration: const InputDecoration(labelText: 'Season (optional)'),
                  items: [
                    const DropdownMenuItem(value: null, child: Text('Any season')),
                    for (final s in _seasons)
                      DropdownMenuItem(value: s, child: Text(s)),
                  ],
                  onChanged: (v) => setState(() => _season = v),
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: _check,
                    icon: const Icon(Icons.shield_outlined),
                    label: const Text('Check price'),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          if (_submitted != null) _ResultSection(query: _submitted!),
        ],
      ),
    );
  }
}

class _ResultSection extends ConsumerWidget {
  const _ResultSection({required this.query});

  final PriceCheckQuery query;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final result = ref.watch(priceCheckProvider(query));
    return result.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Text(
        'Could not check the price. Please try again.',
        style: const TextStyle(color: AppColors.error),
      ),
      data: (r) => _ResultCard(result: r),
    );
  }
}

class _ResultCard extends ConsumerStatefulWidget {
  const _ResultCard({required this.result});

  final PriceCheckResult result;

  @override
  ConsumerState<_ResultCard> createState() => _ResultCardState();
}

class _ResultCardState extends ConsumerState<_ResultCard> {
  bool _reporting = false;
  bool _reported = false;

  Future<void> _report() async {
    final r = widget.result;
    final region = r.region;
    if (region == null || region.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Pick a region above to report this price.')),
      );
      return;
    }
    setState(() => _reporting = true);
    final (failure, _) = await ref.read(antiScamRepositoryProvider).reportScam(
          serviceType: r.serviceType,
          region: region,
          quotedPriceNpr: r.quotedPriceNpr,
          season: r.season,
          description: 'Reported from the fair-price check.',
        );
    if (!mounted) return;
    setState(() {
      _reporting = false;
      _reported = failure == null;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          failure == null
              ? 'Thanks — your report was submitted for review.'
              : failure.message,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final r = widget.result;
    final flagged = r.isLikelyScam;
    // Under-quoting a guide or porter is its own problem, so it gets its own
    // headline rather than being reported as a fair price.
    final underpaying = r.belowFairWage && !flagged;
    final color = flagged
        ? AppColors.error
        : underpaying
            ? AppColors.warning
            : AppColors.success;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                flagged
                    ? Icons.warning_amber_rounded
                    : underpaying
                        ? Icons.volunteer_activism_outlined
                        : Icons.verified_user,
                color: color,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  flagged
                      ? 'This looks overpriced'
                      : underpaying
                          ? 'This is below the fair wage'
                          : 'This price looks fair',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: color,
                  ),
                ),
              ),
              if (r.deviationLabel != null)
                Text(
                  r.deviationLabel!,
                  style: TextStyle(fontWeight: FontWeight.bold, color: color),
                ),
            ],
          ),
          const SizedBox(height: 12),
          _row('You were quoted', 'Rs. ${r.quotedPriceNpr}'),
          if (r.benchmarkPriceNpr != null)
            _row('Fair price', 'Rs. ${r.benchmarkPriceNpr}'),
          if (r.severity != null && r.severity!.isNotEmpty)
            _row('Severity', r.severity!),
          if (r.belowFairWage && r.fairWageMessage != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.warning.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.handshake_outlined,
                      size: 18, color: AppColors.warning),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      r.fairWageMessage!,
                      style: const TextStyle(
                          fontSize: 13, color: AppColors.textPrimary),
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 12),
          if (r.explanation.isNotEmpty) ...[
            const Text('Why', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            for (final line in r.explanation)
              Padding(
                padding: const EdgeInsets.only(bottom: 2),
                child: Text('• $line',
                    style: const TextStyle(color: AppColors.textSecondary)),
              ),
          ],
          Text(
            'Source: ${r.source}',
            style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
          ),
          if (flagged && !_reported) ...[
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _reporting ? null : _report,
                icon: const Icon(Icons.flag_outlined),
                label: Text(_reporting ? 'Submitting...' : 'Report this overcharge'),
              ),
            ),
          ],
          if (_reported)
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: Text('Reported. Thank you for keeping travellers safe.',
                  style: TextStyle(color: AppColors.success)),
            ),
        ],
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.textSecondary)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
