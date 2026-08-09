import '../../domain/entities/chat_message.dart';

/// Maps the core-engine `ChatMessage` JSON to a [ChatMessage] entity.
class ChatMessageModel {
  static ChatMessage fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      room: (json['room'] ?? '') as String,
      senderId: (json['sender'] ?? '').toString(),
      senderName: (json['sender_name'] ?? '') as String,
      body: (json['body'] ?? '') as String,
      createdAt:
          DateTime.tryParse((json['created_at'] ?? '') as String)?.toLocal() ??
              DateTime.now(),
    );
  }
}
