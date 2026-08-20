import 'package:dio/dio.dart';

import '../../../../core/error/api_error_mapper.dart';
import '../../../../core/error/failures.dart';
import '../../domain/entities/destination.dart';
import '../../domain/repositories/destination_repository.dart';
import '../datasources/destination_remote_datasource.dart';

class DestinationRepositoryImpl implements DestinationRepository {
  const DestinationRepositoryImpl(this._remote);

  final DestinationRemoteDataSource _remote;

  @override
  Future<(Failure?, List<Destination>?)> getDestinations({String? search}) async {
    try {
      final models = await _remote.getDestinations(search: search);
      return (null, models.map((m) => m.toEntity()).toList());
    } on DioException catch (e) {
      return (mapDioError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

}
