import { config } from './config';
import { logger } from './logger';

/** Ask the core engine, the domain owner, whether this user belongs to a room. */
export async function authorizeRoom(token: string, room: string): Promise<boolean> {
  try {
    const url = new URL(`${config.coreEngineUrl}/api/v1/chat/threads/authorize/`);
    url.searchParams.set('room', room);
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(5000),
    });
    return response.ok;
  } catch (error) {
    logger.warn('chat room authorization failed', { room, error: String(error) });
    return false;
  }
}
