import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/theme/app_colors.dart';
import '../../domain/entities/trip.dart';
import '../providers/workspace_providers.dart';

/// Day-by-day itinerary for one trip: a budget bar, an AI "suggest" action, an
/// add-item sheet, and a drag-to-reorder list.
class WorkspaceDetailPage extends ConsumerWidget {
  const WorkspaceDetailPage({required this.tripId, super.key});

  final int tripId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final trip = ref.watch(tripDetailProvider(tripId));

    return Scaffold(
      appBar: AppBar(
        title: Text(trip.asData?.value.title ?? 'Trip'),
      ),
      body: trip.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Could not load this trip.',
                  style: TextStyle(color: AppColors.textSecondary)),
              const SizedBox(height: 8),
              OutlinedButton(
                onPressed: () => ref.invalidate(tripDetailProvider(tripId)),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (t) => _TripBody(trip: t),
      ),
    );
  }
}

class _TripBody extends ConsumerStatefulWidget {
  const _TripBody({required this.trip});

  final TravelTrip trip;

  @override
  ConsumerState<_TripBody> createState() => _TripBodyState();
}

class _TripBodyState extends ConsumerState<_TripBody> {
  late final List<TripItem> _items = [...widget.trip.items];
  bool _busy = false;

  int get _tripId => widget.trip.id;

  Future<void> _refresh() async {
    ref.invalidate(tripDetailProvider(_tripId));
    ref.invalidate(tripsProvider);
  }

  Future<void> _reorder(int oldIndex, int newIndex) async {
    setState(() {
      if (newIndex > oldIndex) newIndex -= 1;
      final item = _items.removeAt(oldIndex);
      _items.insert(newIndex, item);
    });
    await ref.read(workspaceRepositoryProvider).reorder(_items);
  }

  Future<void> _suggest() async {
    setState(() => _busy = true);
    final (failure, _) =
        await ref.read(workspaceRepositoryProvider).applyAiSuggestions(_tripId);
    if (!mounted) return;
    setState(() => _busy = false);
    if (failure == null) {
      await _refresh();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Added an AI-suggested itinerary.')),
        );
      }
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(failure.message)));
    }
  }

  Future<void> _delete(TripItem item) async {
    setState(() => _items.removeWhere((i) => i.id == item.id));
    await ref.read(workspaceRepositoryProvider).deleteItem(item.id);
    await _refresh();
  }

  Future<void> _addItem() async {
    final added = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _AddItemSheet(tripId: _tripId, maxDay: widget.trip.tripDays),
    );
    if (added == true) await _refresh();
  }

  double get _planned =>
      _items.fold(0.0, (sum, i) => sum + i.estimatedCostNpr);

  @override
  Widget build(BuildContext context) {
    final budget = widget.trip.totalBudgetNpr;
    final over = _planned > budget;
    final fraction = budget <= 0 ? 0.0 : (_planned / budget).clamp(0, 1).toDouble();

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              LinearProgressIndicator(
                value: fraction,
                minHeight: 8,
                backgroundColor: AppColors.inputFill,
                color: over ? AppColors.error : AppColors.primary,
              ),
              const SizedBox(height: 8),
              Text(
                'Planned Rs. ${_planned.toStringAsFixed(0)} of Rs. ${budget.toStringAsFixed(0)}'
                '${over ? '  •  over budget' : ''}',
                style: TextStyle(
                  color: over ? AppColors.error : AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _addItem,
                      icon: const Icon(Icons.add, size: 18),
                      label: const Text('Add item'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: _busy ? null : _suggest,
                      icon: const Icon(Icons.auto_awesome, size: 18),
                      label: Text(_busy ? 'Working...' : 'Suggest trip'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: _items.isEmpty
              ? const Center(
                  child: Text(
                    'No items yet.\nAdd one, or let AI suggest an itinerary.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                )
              : ReorderableListView.builder(
                  padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
                  itemCount: _items.length,
                  // ignore: deprecated_member_use
                  onReorder: _reorder,
                  itemBuilder: (context, i) {
                    final item = _items[i];
                    return _ItemCard(
                      key: ValueKey(item.id),
                      item: item,
                      onDelete: () => _delete(item),
                    );
                  },
                ),
        ),
      ],
    );
  }
}

class _ItemCard extends StatelessWidget {
  const _ItemCard({required this.item, required this.onDelete, super.key});

  final TripItem item;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: AppColors.primary.withValues(alpha: 0.12),
          child: Text('${item.dayNumber}',
              style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold)),
        ),
        title: Text(item.title, maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Text(
          '${item.itemType} • Rs. ${item.estimatedCostNpr.toStringAsFixed(0)}',
          style: const TextStyle(fontSize: 12.5),
        ),
        trailing: IconButton(
          icon: const Icon(Icons.delete_outline, color: AppColors.textSecondary),
          onPressed: onDelete,
        ),
      ),
    );
  }
}

class _AddItemSheet extends ConsumerStatefulWidget {
  const _AddItemSheet({required this.tripId, required this.maxDay});

  final int tripId;
  final int maxDay;

  @override
  ConsumerState<_AddItemSheet> createState() => _AddItemSheetState();
}

const _itemTypes = <String>['custom', 'destination', 'guide', 'accommodation', 'transport'];

class _AddItemSheetState extends ConsumerState<_AddItemSheet> {
  final _formKey = GlobalKey<FormState>();
  final _title = TextEditingController();
  final _cost = TextEditingController(text: '0');
  String _type = 'custom';
  int _day = 1;
  bool _saving = false;

  @override
  void dispose() {
    _title.dispose();
    _cost.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    final (failure, _) = await ref.read(workspaceRepositoryProvider).addItem(
          tripId: widget.tripId,
          itemType: _type,
          title: _title.text.trim(),
          dayNumber: _day,
          costNpr: double.tryParse(_cost.text.trim()) ?? 0,
        );
    if (!mounted) return;
    setState(() => _saving = false);
    if (failure == null) {
      Navigator.of(context).pop(true);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(failure.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final days = List<int>.generate(widget.maxDay < 1 ? 1 : widget.maxDay, (i) => i + 1);
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
            const Text('Add to itinerary',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            TextFormField(
              controller: _title,
              decoration: const InputDecoration(labelText: 'What is it?'),
              validator: (v) => (v == null || v.trim().isEmpty) ? 'Add a short title' : null,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _type,
                    decoration: const InputDecoration(labelText: 'Type'),
                    items: [
                      for (final t in _itemTypes)
                        DropdownMenuItem(value: t, child: Text(t)),
                    ],
                    onChanged: (v) => setState(() => _type = v ?? _type),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: DropdownButtonFormField<int>(
                    initialValue: _day,
                    decoration: const InputDecoration(labelText: 'Day'),
                    items: [
                      for (final d in days)
                        DropdownMenuItem(value: d, child: Text('Day $d')),
                    ],
                    onChanged: (v) => setState(() => _day = v ?? _day),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _cost,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Estimated cost (NPR)', prefixText: 'Rs. '),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _saving ? null : _save,
                child: Text(_saving ? 'Adding...' : 'Add item'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
