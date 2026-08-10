/**
 * Server-side fetch helpers for the admin dashboard.
 *
 * These run only in React Server Components and Server Actions, so secrets (the
 * ML service key, the staff token) stay on the server and never reach the
 * browser. Reads fail soft — they return null on any error so a page can show an
 * empty state instead of crashing when a backend is down. Writes do the
 * opposite: they return a typed result so the UI can tell the moderator exactly
 * what went wrong.
 */

import 'server-only';

const CORE_API =
  process.env.CORE_API_BASE_URL ?? 'http://localhost:8000/api/v1';
const ML_API = process.env.ANALYTICS_ENGINE_URL ?? 'http://localhost:8001';
const ML_KEY = process.env.ANALYTICS_API_KEY ?? 'change-me-internal-service-token';
// Long-lived staff JWT for protected core-engine reads and moderation writes.
const ADMIN_TOKEN = process.env.ADMIN_API_TOKEN ?? '';

export const hasAdminToken = ADMIN_TOKEN.length > 0;

async function getJson<T>(url: string, headers: Record<string, string>): Promise<T | null> {
  try {
    const res = await fetch(url, { headers, cache: 'no-store' });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/** Read a core-engine endpoint, attaching the staff token when configured. */
export function coreGet<T>(path: string): Promise<T | null> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (ADMIN_TOKEN) headers.Authorization = `Bearer ${ADMIN_TOKEN}`;
  return getJson<T>(`${CORE_API}${path}`, headers);
}

/** Read an analytics-engine (ML) endpoint with the internal service key. */
export function mlGet<T>(path: string): Promise<T | null> {
  return getJson<T>(`${ML_API}${path}`, { 'X-API-Key': ML_KEY });
}

/** POST to an analytics-engine endpoint (the ML service takes its inputs in the body). */
export async function mlPost<T>(path: string, body: unknown): Promise<T | null> {
  try {
    const res = await fetch(`${ML_API}${path}`, {
      method: 'POST',
      headers: { 'X-API-Key': ML_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      cache: 'no-store',
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export type WriteResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

/**
 * POST to a core-engine endpoint as the staff user.
 *
 * Unlike the read helpers this reports failures, because a moderator pressing
 * "verify" needs to know whether it actually happened. The common failure is a
 * missing or expired ADMIN_API_TOKEN, so that case gets its own message rather
 * than a bare 401.
 */
export async function corePost<T>(path: string, body?: unknown): Promise<WriteResult<T>> {
  if (!ADMIN_TOKEN) {
    return {
      ok: false,
      error: 'No staff token configured. Set ADMIN_API_TOKEN to enable moderation.',
    };
  }
  try {
    const res = await fetch(`${CORE_API}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${ADMIN_TOKEN}`,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: 'no-store',
    });

    if (res.status === 401 || res.status === 403) {
      return { ok: false, error: 'Staff token was rejected. Check ADMIN_API_TOKEN is a current admin JWT.' };
    }
    if (!res.ok) {
      const detail = await res.text();
      return { ok: false, error: `Request failed (${res.status}). ${detail.slice(0, 140)}` };
    }
    const text = await res.text();
    return { ok: true, data: (text ? JSON.parse(text) : null) as T };
  } catch (err) {
    const reason = err instanceof Error ? err.message : 'unknown error';
    return { ok: false, error: `Could not reach the core-engine: ${reason}` };
  }
}

/** Pull `results` out of a DRF page, or treat the body as a bare list. */
export function asList<T>(data: unknown): T[] {
  if (data && typeof data === 'object' && Array.isArray((data as { results?: T[] }).results)) {
    return (data as { results: T[] }).results;
  }
  if (Array.isArray(data)) return data as T[];
  return [];
}
