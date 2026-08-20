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
import { cookies } from 'next/headers';

const CORE_API =
  process.env.CORE_API_BASE_URL ?? 'http://localhost:8000/api/v1';
const ML_API = process.env.ANALYTICS_ENGINE_URL ?? 'http://localhost:8001';
const ML_KEY = process.env.ANALYTICS_API_KEY ?? 'change-me-internal-service-token';
// Staff JWT for protected core-engine reads and moderation writes, plus the
// refresh token used to mint a new one when it lapses.
const ADMIN_TOKEN = process.env.ADMIN_API_TOKEN ?? '';
const ADMIN_REFRESH = process.env.ADMIN_REFRESH_TOKEN ?? '';
const ACCESS_COOKIE = 'guideu_admin_access';
const REFRESH_COOKIE = 'guideu_admin_refresh';

export type AdminTokenState = 'active' | 'expired' | 'missing';

/**
 * The real state of the staff token, for the header's service indicator.
 *
 * "Configured" and "working" are not the same thing, and the difference is
 * invisible from the outside: an expired token 401s every request while still
 * looking present in .env. Reporting them separately is the whole point of the
 * indicator.
 */
export async function adminTokenStatus(): Promise<AdminTokenState> {
  const cookieStore = await cookies();
  const configured = Boolean(
    cookieStore.get(ACCESS_COOKIE)?.value || cookieStore.get(REFRESH_COOKIE)?.value
      || ADMIN_TOKEN || ADMIN_REFRESH
  );
  if (!configured) return 'missing';
  return (await bearerToken()) ? 'active' : 'expired';
}

/** Seconds since the epoch at which a JWT expires, or null if unreadable. */
function jwtExpiry(token: string): number | null {
  const payload = token.split('.')[1];
  if (!payload) return null;
  try {
    const json = Buffer.from(payload, 'base64url').toString('utf8');
    const exp = (JSON.parse(json) as { exp?: number }).exp;
    return typeof exp === 'number' ? exp : null;
  } catch {
    return null;
  }
}

/** A token within 30s of expiry is treated as already gone. */
function isExpired(token: string): boolean {
  const exp = jwtExpiry(token);
  return exp !== null && exp * 1000 <= Date.now() + 30_000;
}

// Access token minted from the refresh token during this process's lifetime.
let refreshedToken: string | null = null;

/**
 * The bearer token to send, or '' when there is nothing usable.
 *
 * An expired token is worse than no token at all: DRF authenticates before it
 * checks permissions, so a lapsed bearer makes even AllowAny endpoints answer
 * 401. One stale token therefore blanks the *whole* dashboard — the public
 * festivals calendar and the catalog counters included — which reads as "the
 * database is empty" the morning after a demo. So: drop a dead token, and if a
 * refresh token is configured, quietly mint a replacement.
 */
async function bearerToken(): Promise<string> {
  const cookieStore = await cookies();
  const cookieAccess = cookieStore.get(ACCESS_COOKIE)?.value ?? '';
  const cookieRefresh = cookieStore.get(REFRESH_COOKIE)?.value ?? '';
  if (cookieAccess && !isExpired(cookieAccess)) return cookieAccess;
  if (ADMIN_TOKEN && !isExpired(ADMIN_TOKEN)) return ADMIN_TOKEN;
  if (refreshedToken && !isExpired(refreshedToken)) return refreshedToken;
  const refresh = cookieRefresh || ADMIN_REFRESH;
  if (!refresh || isExpired(refresh)) return '';

  try {
    const res = await fetch(`${CORE_API}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
      cache: 'no-store',
    });
    if (!res.ok) return '';
    const { access } = (await res.json()) as { access?: string };
    refreshedToken = access ?? null;
    return refreshedToken ?? '';
  } catch {
    return '';
  }
}

async function getJson<T>(url: string, headers: Record<string, string>): Promise<T | null> {
  try {
    const res = await fetch(url, { headers, cache: 'no-store' });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/** Read a core-engine endpoint, attaching the staff token when one is usable. */
export async function coreGet<T>(path: string): Promise<T | null> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = await bearerToken();
  if (token) headers.Authorization = `Bearer ${token}`;
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
  const token = await bearerToken();
  if (!token) {
    return {
      ok: false,
      error: 'Your administrator session has expired. Sign in again.',
    };
  }
  try {
    const res = await fetch(`${CORE_API}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
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

/** PATCH to a protected core-engine endpoint. */
export async function corePatch<T>(path: string, body: unknown): Promise<WriteResult<T>> {
  const token = await bearerToken();
  if (!token) return { ok: false, error: 'Your administrator session has expired. Sign in again.' };
  try {
    const res = await fetch(`${CORE_API}${path}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(body),
      cache: 'no-store',
    });
    if (!res.ok) return { ok: false, error: `Request failed (${res.status}). ${(await res.text()).slice(0, 140)}` };
    return { ok: true, data: (await res.json()) as T };
  } catch (error) {
    return { ok: false, error: `Could not reach the core-engine: ${error instanceof Error ? error.message : 'unknown error'}` };
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
