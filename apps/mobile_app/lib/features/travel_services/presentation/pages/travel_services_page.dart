import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../../core/api/api_endpoints.dart';
import '../../../auth/presentation/providers/auth_providers.dart';

class TravelServicesPage extends ConsumerStatefulWidget {
  const TravelServicesPage({required this.serviceType, super.key});
  final String serviceType;

  @override
  ConsumerState<TravelServicesPage> createState() => _TravelServicesPageState();
}

class _TravelServicesPageState extends ConsumerState<TravelServicesPage> {
  final _from = TextEditingController();
  final _to = TextEditingController();
  late Future<List<Map<String, dynamic>>> _future;

  String get _title => switch (widget.serviceType) {
    'HOTEL' => 'Find Hotels',
    'FLIGHT' => 'Flight Tickets',
    _ => 'Bus Tickets',
  };

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  @override
  void dispose() {
    _from.dispose();
    _to.dispose();
    super.dispose();
  }

  Future<List<Map<String, dynamic>>> _load() async {
    final query = <String, dynamic>{'service_type': widget.serviceType};
    if (_from.text.trim().isNotEmpty) {
      query[widget.serviceType == 'HOTEL' ? 'location' : 'origin'] = _from.text
          .trim();
    }
    if (widget.serviceType != 'HOTEL' && _to.text.trim().isNotEmpty) {
      query['destination'] = _to.text.trim();
    }
    final response = await ref
        .read(apiClientProvider)
        .dio
        .get(ApiEndpoints.travelOfferings, queryParameters: query);
    final data = response.data;
    final rows = data is Map
        ? data['results'] as List? ?? const []
        : data as List? ?? const [];
    return rows
        .cast<Map>()
        .map((row) => Map<String, dynamic>.from(row))
        .toList();
  }

  void _search() => setState(() => _future = _load());

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(_title)),
    body: RefreshIndicator(
      onRefresh: () async => _search(),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _from,
            decoration: InputDecoration(
              labelText: widget.serviceType == 'HOTEL'
                  ? 'City or area'
                  : 'From',
              prefixIcon: Icon(
                widget.serviceType == 'HOTEL'
                    ? Icons.location_city
                    : Icons.trip_origin,
              ),
            ),
          ),
          if (widget.serviceType != 'HOTEL') ...[
            const SizedBox(height: 10),
            TextField(
              controller: _to,
              decoration: const InputDecoration(
                labelText: 'To',
                prefixIcon: Icon(Icons.location_on_outlined),
              ),
            ),
          ],
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed: _search,
            icon: const Icon(Icons.search),
            label: const Text('Search availability'),
          ),
          const SizedBox(height: 18),
          FutureBuilder<List<Map<String, dynamic>>>(
            future: _future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Padding(
                  padding: EdgeInsets.all(48),
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              if (snapshot.hasError) {
                return const Padding(
                  padding: EdgeInsets.all(32),
                  child: Center(
                    child: Text('Could not load live availability.'),
                  ),
                );
              }
              final items = snapshot.data ?? const [];
              if (items.isEmpty) {
                return const Padding(
                  padding: EdgeInsets.all(32),
                  child: Center(
                    child: Text(
                      'No matching services found. Try another route or city.',
                    ),
                  ),
                );
              }
              return Column(
                children: [
                  for (final item in items)
                    _OfferingCard(item: item, onBook: () => _book(item)),
                ],
              );
            },
          ),
        ],
      ),
    ),
  );

  Future<void> _book(Map<String, dynamic> offering) async {
    var travellers = 1;
    var units = 1;
    DateTime? start = DateTime.now().add(const Duration(days: 1));
    DateTime? end = start.add(const Duration(days: 1));
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text('Book ${offering['title']}'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (widget.serviceType == 'HOTEL') ...[
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Check-in'),
                  trailing: Text(DateFormat.yMMMd().format(start!)),
                  onTap: () async {
                    final value = await showDatePicker(
                      context: context,
                      firstDate: DateTime.now(),
                      lastDate: DateTime.now().add(const Duration(days: 730)),
                      initialDate: start!,
                    );
                    if (value != null) {
                      setDialogState(() {
                        start = value;
                        if (!end!.isAfter(value)) {
                          end = value.add(const Duration(days: 1));
                        }
                      });
                    }
                  },
                ),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Check-out'),
                  trailing: Text(DateFormat.yMMMd().format(end!)),
                  onTap: () async {
                    final value = await showDatePicker(
                      context: context,
                      firstDate: start!.add(const Duration(days: 1)),
                      lastDate: start!.add(const Duration(days: 730)),
                      initialDate: end!,
                    );
                    if (value != null) setDialogState(() => end = value);
                  },
                ),
              ],
              _Counter(
                label: 'Travellers',
                value: travellers,
                onChanged: (value) => setDialogState(() => travellers = value),
              ),
              if (widget.serviceType == 'HOTEL')
                _Counter(
                  label: 'Rooms',
                  value: units,
                  onChanged: (value) => setDialogState(() => units = value),
                ),
              const SizedBox(height: 8),
              const Text(
                'The server calculates the final amount from current inventory. Your reservation is held until payment.',
                style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Reserve'),
            ),
          ],
        ),
      ),
    );
    if (confirmed != true) return;
    try {
      await ref
          .read(apiClientProvider)
          .dio
          .post(
            ApiEndpoints.travelServiceBookings,
            data: {
              'offering': offering['id'],
              'travellers': travellers,
              'units': widget.serviceType == 'HOTEL' ? units : travellers,
              if (widget.serviceType == 'HOTEL')
                'start_date': DateFormat('yyyy-MM-dd').format(start!),
              if (widget.serviceType == 'HOTEL')
                'end_date': DateFormat('yyyy-MM-dd').format(end!),
            },
          );
      if (!mounted) return;
      setState(() => _future = _load());
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Reservation created. Complete payment from Travel bookings.',
          ),
        ),
      );
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Could not reserve this service. Availability may have changed.',
            ),
          ),
        );
      }
    }
  }
}

class _OfferingCard extends StatelessWidget {
  const _OfferingCard({required this.item, required this.onBook});
  final Map<String, dynamic> item;
  final VoidCallback onBook;
  @override
  Widget build(BuildContext context) {
    final departure = DateTime.tryParse(
      item['departure_at'] as String? ?? '',
    )?.toLocal();
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: AppColors.primary.withValues(alpha: .12),
                  child: Icon(
                    _icon(item['service_type'] as String?),
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item['title'] as String? ?? '',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      Text(
                        item['provider_name'] as String? ?? '',
                        style: const TextStyle(color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              item['service_type'] == 'HOTEL'
                  ? item['location'] as String? ?? ''
                  : '${item['origin']} to ${item['destination']}',
            ),
            if (departure != null)
              Text(
                DateFormat('EEE, MMM d, h:mm a').format(departure),
                style: const TextStyle(color: AppColors.textSecondary),
              ),
            const SizedBox(height: 10),
            Row(
              children: [
                Text(
                  '${item['currency']} ${item['unit_price']}',
                  style: const TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                    color: AppColors.primaryDark,
                  ),
                ),
                Text(
                  item['service_type'] == 'HOTEL'
                      ? ' / room / night'
                      : ' / traveller',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                  ),
                ),
                const Spacer(),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(92, 48),
                  ),
                  onPressed: onBook,
                  child: const Text('Book'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  static IconData _icon(String? type) => switch (type) {
    'HOTEL' => Icons.hotel,
    'FLIGHT' => Icons.flight,
    _ => Icons.directions_bus,
  };
}

class _Counter extends StatelessWidget {
  const _Counter({
    required this.label,
    required this.value,
    required this.onChanged,
  });
  final String label;
  final int value;
  final ValueChanged<int> onChanged;
  @override
  Widget build(BuildContext context) => Row(
    children: [
      Expanded(child: Text(label)),
      IconButton(
        onPressed: value > 1 ? () => onChanged(value - 1) : null,
        icon: const Icon(Icons.remove_circle_outline),
      ),
      Text('$value'),
      IconButton(
        onPressed: value < 10 ? () => onChanged(value + 1) : null,
        icon: const Icon(Icons.add_circle_outline),
      ),
    ],
  );
}
