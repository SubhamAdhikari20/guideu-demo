import '../../domain/entities/chat_thread.dart';

/// Maps the core-engine `ChatThread` JSON to a [ChatThread] entity.
class ChatThreadModel {
  static ChatThread fromJson(Map<String, dynamic> json) {
    final last = json['last_message'];
    return ChatThread(
      id: (json['id'] ?? 0) as int,
      room: (json['room'] ?? '') as String,
      unreadCount: (json['unread_count'] ?? 0) as int,
      lastMessageBody:
          last is Map<String, dynamic> ? last['body'] as String? : null,
      updatedAt:
          DateTime.tryParse((json['updated_at'] ?? '') as String)?.toLocal(),
    );
  }
}
