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
  final _joined = StreamController<bool>.broadcast();
  final _errors = StreamController<String>.broadcast();
  final Set<String> _joinedRooms = <String>{};

  Stream<ChatMessage> get messages => _messages.stream;
  Stream<bool> get connectionState => _connected.stream;
  Stream<bool> get joinedState => _joined.stream;
  Stream<String> get errors => _errors.stream;

  void connect(String token, {required String room}) {
    if (_socket != null) return;
    final socket = io.io(
      ApiEndpoints.realtimeBaseUrl,
      io.OptionBuilder()
          .setTransports(['websocket'])
          .disableAutoConnect()
          .setAuth(<String, dynamic>{'token': token})
          .build(),
    );

    void joinRoom() => socket.emit('chat:join', {'room': room});

    socket.onConnect((_) {
      _connected.add(true);
      joinRoom();
    });
    socket.onDisconnect((_) {
      _connected.add(false);
      _joinedRooms.clear();
      _joined.add(false);
    });
    socket.onConnectError((error) {
      _connected.add(false);
      _errors.add('Could not connect to live chat.');
    });
    socket.on('chat:joined', (data) {
      if (data is Map && data['room'] == room) {
        _joinedRooms.add(room);
        _joined.add(true);
      }
    });
    socket.on('error:message', (data) {
      final detail = data is Map ? data['detail']?.toString() : null;
      _errors.add(detail ?? 'Live chat could not complete that action.');
    });
    socket.on('chat:message', (data) {
      if (data is! Map) return;
      _messages.add(
        ChatMessage(
          room: (data['room'] ?? '') as String,
          senderId: (data['from'] ?? '').toString(),
          body: (data['body'] ?? '') as String,
          createdAt:
              DateTime.tryParse((data['ts'] ?? '') as String)?.toLocal() ??
              DateTime.now(),
        ),
      );
    });

    _socket = socket;
    socket.connect();
  }

  bool send(String room, String body) {
    final socket = _socket;
    if (socket == null || !socket.connected || !_joinedRooms.contains(room)) {
      return false;
    }
    socket.emit('chat:message', {'room': room, 'body': body});
    return true;
  }

  void dispose() {
    _socket?.dispose();
    _socket = null;
    _joinedRooms.clear();
    _messages.close();
    _connected.close();
    _joined.close();
    _errors.close();
  }
}
