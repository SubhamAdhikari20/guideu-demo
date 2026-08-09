import 'package:dio/dio.dart';

import '../../../../core/error/failures.dart';
import '../../domain/entities/chat_message.dart';
import '../../domain/entities/chat_thread.dart';
import '../../domain/repositories/chat_repository.dart';
import '../datasources/chat_remote_datasource.dart';

class ChatRepositoryImpl implements ChatRepository {
  const ChatRepositoryImpl(this._remote);

  final ChatRemoteDataSource _remote;

  @override
  Future<(Failure?, List<ChatThread>?)> getThreads() async {
    try {
      return (null, await _remote.getThreads());
    } on DioException catch (e) {
      return (_mapError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  @override
  Future<(Failure?, List<ChatMessage>?)> getHistory(String room) async {
    try {
      return (null, await _remote.getHistory(room));
    } on DioException catch (e) {
      return (_mapError(e), null);
    } catch (e) {
      return (ServerFailure(e.toString()), null);
    }
  }

  Failure _mapError(DioException e) {
    if (e.type == DioExceptionType.connectionError ||
        e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout) {
      return const NetworkFailure();
    }
    return ServerFailure('Could not load messages.', statusCode: e.response?.statusCode);
  }
}
