import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../../core/widgets/empty_state.dart';
import '../../../../core/widgets/error_retry.dart';
import '../../domain/entities/trip.dart';
import '../providers/workspace_providers.dart';
import 'workspace_detail_page.dart';

/// "My Trips" — the tourist's travel workspaces. Tap a trip to plan it, or use
/// the + button to start a new one.
class WorkspacesListPage extends ConsumerWidget {
  const WorkspacesListPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final trips = ref.watch(tripsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('My Trips')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _createTrip(context, ref),
        icon: const Icon(Icons.add),
        label: const Text('New trip'),
      ),
      body: trips.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => ErrorRetry(
          message: 'Could not load your trips.',
          onRetry: () => ref.invalidate(tripsProvider),
        ),
        data: (items) {
          if (items.isEmpty) {
            return EmptyState(
              icon: Icons.map_outlined,
              title: 'No trips yet',
              message: 'Start planning your journey across Nepal.',
              actionLabel: 'New trip',
              onAction: () => _createTrip(context, ref),
            );
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(tripsProvider),
            child: ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 90),
              itemCount: items.length,
              itemBuilder: (context, i) => _TripCard(
                trip: items[i],
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => WorkspaceDetailPage(tripId: items[i].id),
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Future<void> _createTrip(BuildContext context, WidgetRef ref) async {
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => const _CreateTripSheet(),
    );
    if (created == true) ref.invalidate(tripsProvider);
  }
}

class _TripCard extends StatelessWidget {
  const _TripCard({required this.trip, required this.onTap});

  final TravelTrip trip;
  final VoidCallback onTap;

  String _d(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(trip.title,
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Row(
                children: [
                  const Icon(Icons.calendar_today, size: 14, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Text('${_d(trip.startDate)} → ${_d(trip.endDate)}',
                      style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5)),
                  const Spacer(),
                  Text('${trip.tripDays} days',
                      style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5)),
                ],
              ),
              const SizedBox(height: 10),
              LinearProgressIndicator(
                value: trip.budgetFraction,
                minHeight: 6,
                backgroundColor: AppColors.inputFill,
                color: trip.isOverBudget ? AppColors.error : AppColors.primary,
              ),
              const SizedBox(height: 6),
              Text(
                'Planned Rs. ${trip.totalPlannedCostNpr.toStringAsFixed(0)} of Rs. ${trip.totalBudgetNpr.toStringAsFixed(0)} • ${trip.itemCount} items',
                style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CreateTripSheet extends ConsumerStatefulWidget {
  const _CreateTripSheet();

  @override
  ConsumerState<_CreateTripSheet> createState() => _CreateTripSheetState();
}

class _CreateTripSheetState extends ConsumerState<_CreateTripSheet> {
  final _formKey = GlobalKey<FormState>();
  final _title = TextEditingController();
  final _budget = TextEditingController(text: '50000');
  DateTime _start = DateTime.now().add(const Duration(days: 7));
  DateTime _end = DateTime.now().add(const Duration(days: 12));
  bool _saving = false;

  @override
  void dispose() {
    _title.dispose();
    _budget.dispose();
    super.dispose();
  }

  Future<void> _pickDate({required bool isStart}) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: isStart ? _start : _end,
      firstDate: DateTime.now().subtract(const Duration(days: 1)),
      lastDate: DateTime.now().add(const Duration(days: 730)),
    );
    if (picked == null) return;
    setState(() {
      if (isStart) {
        _start = picked;
        if (_end.isBefore(_start)) _end = _start.add(const Duration(days: 1));
      } else {
        _end = picked;
      }
    });
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    if (_end.isBefore(_start)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('End date must be after the start date.')),
      );
      return;
    }
    setState(() => _saving = true);
    final (failure, _) = await ref.read(workspaceRepositoryProvider).createTrip(
          title: _title.text.trim(),
          startDate: _start,
          endDate: _end,
          budgetNpr: double.tryParse(_budget.text.trim()) ?? 0,
        );
    if (!mounted) return;
    setState(() => _saving = false);
    if (failure == null) {
      Navigator.of(context).pop(true);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(failure.message)));
    }
  }

  String _d(DateTime d) => '${d.day}/${d.month}/${d.year}';

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16, right: 16, top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('New trip',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            TextFormField(
              controller: _title,
              decoration: const InputDecoration(labelText: 'Trip title'),
              validator: (v) => (v == null || v.trim().isEmpty) ? 'Give your trip a name' : null,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _pickDate(isStart: true),
                    icon: const Icon(Icons.event, size: 18),
                    label: Text('Start ${_d(_start)}'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _pickDate(isStart: false),
                    icon: const Icon(Icons.event, size: 18),
                    label: Text('End ${_d(_end)}'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _budget,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Budget (NPR)', prefixText: 'Rs. '),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _saving ? null : _save,
                child: Text(_saving ? 'Creating...' : 'Create trip'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
