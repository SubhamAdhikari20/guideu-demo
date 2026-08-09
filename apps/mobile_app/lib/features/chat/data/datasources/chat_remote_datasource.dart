import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../models/chat_message_model.dart';
import '../models/chat_thread_model.dart';
import '../../domain/entities/chat_message.dart';
import '../../domain/entities/chat_thread.dart';

/// Reads chat history and threads from the core-engine. Live delivery is the
/// socket's job (see [ChatSocketDataSource]); this is the durable backlog.
class ChatRemoteDataSource {
  const ChatRemoteDataSource(this._dio);

  final Dio _dio;

  Future<List<ChatThread>> getThreads() async {
    final resp = await _dio.get(ApiEndpoints.chatThreads);
    return _results(resp.data)
        .map((e) => ChatThreadModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<ChatMessage>> getHistory(String room) async {
    final resp = await _dio.get(
      ApiEndpoints.chatMessages,
      queryParameters: <String, dynamic>{'room': room},
    );
    return _results(resp.data)
        .map((e) => ChatMessageModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  List<dynamic> _results(dynamic data) {
    if (data is Map && data['results'] is List) {
      return data['results'] as List<dynamic>;
    }
    if (data is List) return data;
    return const [];
  }
}
