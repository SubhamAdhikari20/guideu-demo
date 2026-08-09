import 'dart:async';

import 'package:socket_io_client/socket_io_client.dart' as io;

import '../../../../core/api/api_endpoints.dart';
import '../../domain/entities/chat_message.dart';

/// Thin wrapper over the Socket.IO client for live chat with the realtime-engine.
///
/// The server authenticates the handshake with the JWT, persists each delivered
/// message (so it shows up in REST history later), and echoes messages back to
/// the room — including the sender — so we simply render whatever arrives.
class ChatSocketDataSource {
  io.Socket? _socket;
  final _messages = StreamController<ChatMessage>.broadcast();
  final _connected = StreamController<bool>.broadcast();

  Stream<ChatMessage> get messages => _messages.stream;
  Stream<bool> get connectionState => _connected.stream;

  void connect(String token) {
    if (_socket != null) return;
    final socket = io.io(
      ApiEndpoints.realtimeBaseUrl,
      io.OptionBuilder()
          .setTransports(['websocket'])
          .disableAutoConnect()
          .setAuth(<String, dynamic>{'token': token})
          .build(),
    );

    socket.onConnect((_) => _connected.add(true));
    socket.onDisconnect((_) => _connected.add(false));
    socket.on('chat:message', (data) {
      if (data is! Map) return;
      _messages.add(
        ChatMessage(
          room: (data['room'] ?? '') as String,
          senderId: (data['from'] ?? '').toString(),
          body: (data['body'] ?? '') as String,
          createdAt: DateTime.tryParse((data['ts'] ?? '') as String)?.toLocal() ??
              DateTime.now(),
        ),
      );
    });

    _socket = socket;
    socket.connect();
  }

  void join(String room) => _socket?.emit('chat:join', {'room': room});

  void send(String room, String body) =>
      _socket?.emit('chat:message', {'room': room, 'body': body});

  void dispose() {
    _socket?.dispose();
    _socket = null;
    _messages.close();
    _connected.close();
  }
}
