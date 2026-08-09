import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/theme/app_colors.dart';
import '../providers/chat_providers.dart';
import 'chat_room_page.dart';

/// The chat inbox — every conversation the user is part of. New conversations
/// are started from a booking ("Message"), then appear here.
class ChatThreadsPage extends ConsumerWidget {
  const ChatThreadsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final threads = ref.watch(chatThreadsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Messages')),
      body: threads.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'Could not load your messages.',
                style: TextStyle(color: AppColors.textSecondary),
              ),
              const SizedBox(height: 8),
              OutlinedButton(
                onPressed: () => ref.invalidate(chatThreadsProvider),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (items) {
          if (items.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'No conversations yet.\nStart one from a booking to chat with your guide.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppColors.textSecondary),
                ),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(chatThreadsProvider),
            child: ListView.separated(
              itemCount: items.length,
              separatorBuilder: (_, _) => const Divider(height: 1),
              itemBuilder: (context, i) {
                final t = items[i];
                return ListTile(
                  leading: CircleAvatar(
                    backgroundColor: AppColors.primary.withValues(alpha: 0.12),
                    child: const Icon(Icons.chat_bubble_outline,
                        color: AppColors.primary),
                  ),
                  title: Text(t.title),
                  subtitle: Text(
                    t.lastMessageBody ?? 'No messages yet',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  trailing: t.unreadCount > 0
                      ? CircleAvatar(
                          radius: 11,
                          backgroundColor: AppColors.gold,
                          child: Text(
                            '${t.unreadCount}',
                            style: const TextStyle(
                                fontSize: 11, color: Colors.white),
                          ),
                        )
                      : null,
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) =>
                          ChatRoomPage(room: t.room, title: t.title),
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
