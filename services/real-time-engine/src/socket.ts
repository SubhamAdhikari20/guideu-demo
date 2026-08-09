import { Server, Socket } from 'socket.io';

import { verifyToken } from './auth';
import { persistMessage } from './chatHistory';
import { logger } from './logger';
import { rooms } from './redisBridge';
import { AvailabilityPayload, ChatJoinPayload, ChatMessagePayload, AuthedUser } from './types';

const PRESENCE_ROOM = 'presence';

/** JWT handshake middleware: reject unauthenticated sockets. */
function authMiddleware(socket: Socket, next: (err?: Error) => void): void {
  const token =
    (socket.handshake.auth?.token as string | undefined) ??
    (socket.handshake.query?.token as string | undefined);
  if (!token) return next(new Error('unauthorized: missing token'));
  const user = verifyToken(token);
  if (!user) return next(new Error('unauthorized: invalid token'));
  socket.data.user = user;
  socket.data.token = token; // kept so we can persist chat history as this user
  next();
}

function joinIdentityRooms(socket: Socket, user: AuthedUser): void {
  socket.join(rooms.user(user.userId));
  if (user.role === 'GUIDE') socket.join(rooms.guide(user.userId));
  else socket.join(rooms.tourist(user.userId));
}

export function attachSocketHandlers(io: Server): void {
  io.use(authMiddleware);

  io.on('connection', (socket: Socket) => {
    const user = socket.data.user as AuthedUser;
    joinIdentityRooms(socket, user);
    logger.info('socket connected', { userId: user.userId, sid: socket.id });
    socket.to(PRESENCE_ROOM).emit('presence:update', { user_id: user.userId, online: true });

    socket.on('presence:subscribe', () => socket.join(PRESENCE_ROOM));

    // --- Chat: room-scoped messaging (e.g. tourist <-> guide for a booking) ---
    socket.on('chat:join', ({ room }: ChatJoinPayload) => {
      if (typeof room !== 'string' || !room.startsWith('booking:')) {
        socket.emit('error:message', { detail: 'Invalid chat room.' });
        return;
      }
      socket.join(room);
      socket.emit('chat:joined', { room });
    });

    socket.on('chat:message', ({ room, body }: ChatMessagePayload) => {
      if (!room || !body || !socket.rooms.has(room)) {
        socket.emit('error:message', { detail: 'Join the room before sending.' });
        return;
      }
      const text = String(body).slice(0, 4000);
      io.to(room).emit('chat:message', {
        room,
        from: user.userId,
        body: text,
        ts: new Date().toISOString(),
      });
      // Store it for history (best-effort; never blocks live delivery).
      void persistMessage(socket.data.token as string, room, text);
    });

    // --- Guide availability (live) ---
    socket.on('guide:availability', ({ available }: AvailabilityPayload) => {
      io.to(PRESENCE_ROOM).emit('guide:availability', {
        user_id: user.userId,
        available: Boolean(available),
        ts: new Date().toISOString(),
      });
    });

    socket.on('disconnect', () => {
      socket.to(PRESENCE_ROOM).emit('presence:update', { user_id: user.userId, online: false });
      logger.info('socket disconnected', { userId: user.userId, sid: socket.id });
    });
  });
}
