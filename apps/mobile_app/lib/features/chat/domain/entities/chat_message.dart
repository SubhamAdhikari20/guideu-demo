/// A single chat message, mapped from either the REST history
/// (`chat/messages`) or a live `chat:message` socket event.
class ChatMessage {
  const ChatMessage({
    required this.room,
    required this.senderId,
    required this.body,
    required this.createdAt,
    this.senderName = '',
  });

  final String room;
  final String senderId; // kept as String so REST (int id) and socket agree
  final String body;
  final DateTime createdAt;
  final String senderName;

  bool isMine(String currentUserId) => senderId == currentUserId;
}
