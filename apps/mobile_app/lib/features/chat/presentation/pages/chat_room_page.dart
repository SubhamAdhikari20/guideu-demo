import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../auth/presentation/providers/auth_providers.dart';
import '../../../auth/presentation/providers/auth_state.dart';
import '../../data/datasources/chat_socket_datasource.dart';
import '../../domain/entities/chat_message.dart';
import '../providers/chat_providers.dart';

/// A live conversation for one room (e.g. `booking:42`). Loads the REST history
/// then streams live messages over the Socket.IO connection.
class ChatRoomPage extends ConsumerStatefulWidget {
  const ChatRoomPage({required this.room, required this.title, super.key});

  final String room;
  final String title;

  @override
  ConsumerState<ChatRoomPage> createState() => _ChatRoomPageState();
}

class _ChatRoomPageState extends ConsumerState<ChatRoomPage> {
  final _socket = ChatSocketDataSource();
  final _input = TextEditingController();
  final _scroll = ScrollController();
  final List<ChatMessage> _messages = [];
  StreamSubscription<ChatMessage>? _sub;
  StreamSubscription<bool>? _connectionSub;
  StreamSubscription<bool>? _joinedSub;
  StreamSubscription<String>? _errorSub;
  bool _loading = true;
  bool _connected = false;
  bool _joined = false;
  String? _socketError;
  String _currentUserId = '';

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final auth = ref.read(authControllerProvider);
    if (auth is AuthAuthenticated) _currentUserId = auth.user.id;

    final (_, history) = await ref
        .read(chatRepositoryProvider)
        .getHistory(widget.room);
    if (!mounted) return;
    setState(() {
      if (history != null) _messages.addAll(history);
      _loading = false;
    });
    _scrollToBottom();

    final token = await ref.read(tokenStorageProvider).getAccessToken();
    if (token == null || token.isEmpty || !mounted) return;
    _connectionSub = _socket.connectionState.listen((connected) {
      if (mounted) setState(() => _connected = connected);
    });
    _joinedSub = _socket.joinedState.listen((joined) {
      if (mounted) {
        setState(() {
          _joined = joined;
          _socketError = null;
        });
      }
    });
    _errorSub = _socket.errors.listen((message) {
      if (mounted) setState(() => _socketError = message);
    });
    _sub = _socket.messages.listen((m) {
      if (m.room != widget.room || !mounted) return;
      setState(() => _messages.add(m));
      _scrollToBottom();
    });
    _socket.connect(token, room: widget.room);
  }

  void _send() {
    final text = _input.text.trim();
    if (text.isEmpty) return;
    if (!_socket.send(widget.room, text)) {
      setState(
        () => _socketError = 'Wait for live chat to connect before sending.',
      );
      return;
    }
    _input.clear();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.jumpTo(_scroll.position.maxScrollExtent);
      }
    });
  }

  @override
  void dispose() {
    _sub?.cancel();
    _connectionSub?.cancel();
    _joinedSub?.cancel();
    _errorSub?.cancel();
    _socket.dispose();
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: Column(
        children: [
          _ConnectionBanner(
            connected: _connected,
            joined: _joined,
            error: _socketError,
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _messages.isEmpty
                ? const Center(
                    child: Text(
                      'No messages yet. Say hello!',
                      style: TextStyle(color: AppColors.textSecondary),
                    ),
                  )
                : ListView.builder(
                    controller: _scroll,
                    padding: const EdgeInsets.all(12),
                    itemCount: _messages.length,
                    itemBuilder: (context, i) => _Bubble(
                      message: _messages[i],
                      isMine: _messages[i].isMine(_currentUserId),
                    ),
                  ),
          ),
          _Composer(controller: _input, onSend: _send, enabled: _joined),
        ],
      ),
    );
  }
}

class _ConnectionBanner extends StatelessWidget {
  const _ConnectionBanner({
    required this.connected,
    required this.joined,
    this.error,
  });
  final bool connected;
  final bool joined;
  final String? error;

  @override
  Widget build(BuildContext context) {
    if (joined && error == null) return const SizedBox.shrink();
    final message =
        error ??
        (connected
            ? 'Joining secure conversation...'
            : 'Connecting to live chat...');
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      color: error == null
          ? AppColors.gold.withValues(alpha: .12)
          : AppColors.error.withValues(alpha: .10),
      child: Row(
        children: [
          if (error == null)
            const SizedBox(
              width: 14,
              height: 14,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          else
            const Icon(Icons.error_outline, size: 18, color: AppColors.error),
          const SizedBox(width: 9),
          Expanded(child: Text(message, style: const TextStyle(fontSize: 12))),
        ],
      ),
    );
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble({required this.message, required this.isMine});

  final ChatMessage message;
  final bool isMine;

  String get _time {
    final t = message.createdAt;
    final h = t.hour.toString().padLeft(2, '0');
    final m = t.minute.toString().padLeft(2, '0');
    return '$h:$m';
  }

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: isMine ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.72,
        ),
        decoration: BoxDecoration(
          color: isMine ? AppColors.primary : AppColors.inputFill,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          crossAxisAlignment: isMine
              ? CrossAxisAlignment.end
              : CrossAxisAlignment.start,
          children: [
            Text(
              message.body,
              style: TextStyle(
                color: isMine ? Colors.white : AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              _time,
              style: TextStyle(
                fontSize: 10,
                color: isMine ? Colors.white70 : AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  const _Composer({
    required this.controller,
    required this.onSend,
    required this.enabled,
  });

  final TextEditingController controller;
  final VoidCallback onSend;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 6, 12, 6),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                enabled: enabled,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => onSend(),
                decoration: InputDecoration(
                  hintText: enabled ? 'Type a message' : 'Connecting...',
                  filled: true,
                  fillColor: AppColors.inputFill,
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 10,
                  ),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            CircleAvatar(
              backgroundColor: AppColors.primary,
              child: IconButton(
                icon: const Icon(Icons.send, color: Colors.white, size: 20),
                onPressed: enabled ? onSend : null,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
