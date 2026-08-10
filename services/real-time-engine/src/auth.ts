import jwt from 'jsonwebtoken';

import { config } from './config';
import { AuthedUser } from './types';

/**
 * Verify a SimpleJWT access token using the shared HS256 secret.
 *
 * Django's default SimpleJWT payload carries `user_id` (and `token_type`). We
 * trust only the identity; the core engine remains the source of truth for
 * roles and permissions.
 *
 * `user_id` is accepted as either a number or a numeric string: SimpleJWT
 * serialises the claim as a string (so the format also suits UUID primary
 * keys), while Django's Redis events publish the integer pk. Requiring a number
 * here rejected every genuine token and silently disabled live chat.
 */
export function verifyToken(token: string): AuthedUser | null {
  try {
    const decoded = jwt.verify(token, config.jwtSecret, { algorithms: ['HS256'] }) as Record<string, unknown>;
    const userId = normaliseUserId(decoded.user_id);
    if (userId === null) return null;
    return { userId, role: typeof decoded.role === 'string' ? decoded.role : undefined };
  } catch {
    return null;
  }
}

/** Accept `23` or `"23"`; keep non-numeric ids (e.g. UUIDs) as strings. */
function normaliseUserId(raw: unknown): number | string | null {
  if (typeof raw === 'number' && Number.isFinite(raw)) return raw;
  if (typeof raw === 'string' && raw.length > 0) {
    // Normalise numeric strings so room names match the ids Django publishes.
    return /^\d+$/.test(raw) ? Number(raw) : raw;
  }
  return null;
}
