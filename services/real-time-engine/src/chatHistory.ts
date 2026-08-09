import { config } from './config';
import { logger } from './logger';

/**
 * Persist a delivered chat message to the core-engine so it survives in history.
 *
 * We post as the sending user (their JWT), so the core-engine applies the same
 * room-membership rules as any REST call. This is best-effort: a failure here is
 * logged but never blocks the live message that was already delivered.
 */
export async function persistMessage(token: string, room: string, body: string): Promise<void> {
  try {
    const res = await fetch(`${config.coreEngineUrl}/api/v1/chat/messages/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ room, body }),
    });
    if (!res.ok) {
      logger.warn('chat history persist rejected', { room, status: res.status });
    }
  } catch (err) {
    logger.warn('chat history persist failed', { room, err: String(err) });
  }
}
