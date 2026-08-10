import { createClient } from 'redis';
import { Server } from 'socket.io';

import { config } from './config';
import { logger } from './logger';
import {
  BookingEvent,
  CHANNELS,
  DomainEvent,
  NotificationEvent,
  PaymentEvent,
  PermitEvent,
} from './types';

export const rooms = {
  user: (id: number | string) => `user:${id}`,
  tourist: (id: number | string) => `tourist:${id}`,
  guide: (id: number | string) => `guide:${id}`,
  /**
   * Booking rooms are keyed by the booking's **primary key**, not its public
   * reference. That is what the Flutter app joins (`booking:${booking.id}`) and
   * what the core-engine parses when it resolves a room to its participants.
   * This used to fan out on `booking_reference`, so every booking push went to a
   * room nobody was in and the core-engine rejected the matching chat history
   * write with 403.
   */
  booking: (id: number | string) => `booking:${id}`,
};

function handleBooking(io: Server, ev: BookingEvent): void {
  const targets = [rooms.user(ev.tourist_id), rooms.booking(ev.booking_id)];
  if (ev.assigned_guide_id) targets.push(rooms.user(ev.assigned_guide_id));
  io.to(targets).emit('booking:update', ev);
}

function handlePayment(io: Server, ev: PaymentEvent): void {
  io.to(rooms.user(ev.user_id)).emit('payment:update', ev);
}

function handlePermit(io: Server, ev: PermitEvent): void {
  io.to(rooms.user(ev.applicant_id)).emit('permit:update', ev);
}

function handleNotification(io: Server, ev: NotificationEvent): void {
  io.to(rooms.user(ev.user_id)).emit('notification:new', ev);
}

/** How many times to retry the initial Redis connection before giving up. */
const MAX_CONNECT_RETRIES = 2;

/**
 * Subscribe to the Django Redis event bus and fan messages out to the relevant
 * Socket.IO rooms. This is the consumer side of the contract Django's
 * `post_save` signals already publish (see docs/api-contracts.md).
 *
 * **Optional by design.** Chat runs entirely over Socket.IO; Redis only carries
 * Django's booking / payment / permit / notification pushes. If it is not
 * running, this resolves to a no-op so the socket server still serves chat.
 * Previously the default client retried forever, so `connect()` never settled
 * and the caller never reached `listen()` — the service looked alive but had
 * bound no port at all.
 */
export async function startRedisBridge(io: Server): Promise<() => Promise<void>> {
  const noop = async (): Promise<void> => undefined;

  const subscriber = createClient({
    url: config.redisUrl,
    socket: {
      // Fail fast rather than retrying into an unbound server.
      reconnectStrategy: (retries) => (retries > MAX_CONNECT_RETRIES ? false : 200),
    },
  });
  // Without a listener an emitted 'error' would crash the process.
  subscriber.on('error', (err) => logger.debug('redis subscriber error', { err: String(err) }));

  try {
    await subscriber.connect();
  } catch (err) {
    logger.warn('Redis unavailable — chat will work, but Django event push is disabled', {
      url: config.redisUrl,
      err: String(err),
    });
    return noop;
  }

  const dispatch = (channel: string, raw: string): void => {
    let ev: DomainEvent;
    try {
      ev = JSON.parse(raw) as DomainEvent;
    } catch (err) {
      logger.warn('could not parse event', { channel, err: String(err) });
      return;
    }
    logger.debug('event in', { channel, event: ev.event });
    switch (channel) {
      case CHANNELS.BOOKING:
        return handleBooking(io, ev as BookingEvent);
      case CHANNELS.PAYMENT:
        return handlePayment(io, ev as PaymentEvent);
      case CHANNELS.PERMIT:
        return handlePermit(io, ev as PermitEvent);
      case CHANNELS.NOTIFICATION:
        return handleNotification(io, ev as NotificationEvent);
      default:
        logger.debug('unhandled channel', { channel });
    }
  };

  const channels = [CHANNELS.BOOKING, CHANNELS.PAYMENT, CHANNELS.PERMIT, CHANNELS.NOTIFICATION, CHANNELS.USER];
  await Promise.all(channels.map((ch) => subscriber.subscribe(ch, (msg) => dispatch(ch, msg))));
  logger.info('subscribed to Redis event bus', { channels });

  return async () => {
    await subscriber.quit();
  };
}
