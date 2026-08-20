import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../models/booking_model.dart';
import '../models/tour_package_model.dart';

/// Talks to the core-engine bookings endpoints over Dio.
class BookingRemoteDataSource {
  const BookingRemoteDataSource(this._dio);

  final Dio _dio;

  Future<List<TourPackageModel>> getPackages({String? search}) async {
    final resp = await _dio.get(
      ApiEndpoints.packages,
      queryParameters: <String, dynamic>{
        if (search != null && search.isNotEmpty) 'search': search,
      },
    );
    return _resultsOf(resp.data)
        .map((e) => TourPackageModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<BookingModel> createBooking({
    required int packageId,
    required DateTime startDate,
    required DateTime endDate,
    String notes = '',
  }) async {
    final resp = await _dio.post(
      ApiEndpoints.bookings,
      data: <String, dynamic>{
        'tour_package': packageId,
        'start_date': _date(startDate),
        'end_date': _date(endDate),
        if (notes.isNotEmpty) 'notes': notes,
      },
    );
    return BookingModel.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<List<BookingModel>> getMyBookings() async {
    final resp = await _dio.get(ApiEndpoints.bookings);
    return _resultsOf(resp.data)
        .map((e) => BookingModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<BookingModel> cancelBooking(int bookingId) async {
    final resp = await _dio.post('${ApiEndpoints.bookings}$bookingId/cancel/');
    return BookingModel.fromJson(resp.data as Map<String, dynamic>);
  }

  String _date(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-'
      '${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';

  List<dynamic> _resultsOf(dynamic data) {
    if (data is Map && data['results'] is List) {
      return data['results'] as List<dynamic>;
    }
    if (data is List) return data;
    return const [];
  }
}
