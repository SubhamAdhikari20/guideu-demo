import '../../../../core/error/failures.dart';
import '../entities/chat_message.dart';
import '../entities/chat_thread.dart';

/// Durable chat history (live messages travel over the socket separately).
abstract interface class ChatRepository {
  Future<(Failure?, List<ChatThread>?)> getThreads();

  Future<(Failure?, List<ChatMessage>?)> getHistory(String room);
}
