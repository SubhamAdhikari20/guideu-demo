import 'package:dio/dio.dart';

import '../../../../core/error/api_error_mapper.dart';
import '../../../../core/error/failures.dart';
import '../../domain/entities/guide.dart';
import '../../domain/repositories/guide_repository.dart';
import '../datasources/guide_remote_datasource.dart';

class GuideRepositoryImpl implements GuideRepository {
  const GuideRepositoryImpl(this._remote);

  final GuideRemoteDataSource _remote;

  @override
  Future<(Failure?, List<Guide>?)> getGuides({String? search}) async {
    try {
      final models = await _remote.getGuides(search: search);
      return (null, models.map((m) => m.toEntity()).toList());
    } on DioException catch (e) {
      return (mapDioError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

}
