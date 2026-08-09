/// A conversation in the chat inbox, mapped from `chat/threads`.
class ChatThread {
  const ChatThread({
    required this.id,
    required this.room,
    required this.unreadCount,
    this.lastMessageBody,
    this.updatedAt,
  });

  final int id;
  final String room;
  final int unreadCount;
  final String? lastMessageBody;
  final DateTime? updatedAt;

  /// A readable title from the room key, e.g. "booking:42" -> "Booking #42".
  String get title {
    if (room.startsWith('booking:')) {
      return 'Booking #${room.substring('booking:'.length)}';
    }
    return room;
  }
}
