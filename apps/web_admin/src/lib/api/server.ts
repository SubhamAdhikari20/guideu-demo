/**
 * Server-side fetch helpers for the admin dashboard.
 *
 * These run only in React Server Components, so secrets (the ML service key, an
 * admin token) stay on the server and never reach the browser. Each helper
 * fails soft — it returns null on any error so a page can show an empty state
 * instead of crashing when a backend is down.
 */

const CORE_API =
  process.env.CORE_API_BASE_URL ?? 'http://localhost:8000/api/v1';
const ML_API = process.env.ANALYTICS_ENGINE_URL ?? 'http://localhost:8001';
const ML_KEY = process.env.ANALYTICS_API_KEY ?? '';
// Optional long-lived admin JWT for protected core-engine reads (scam reports).
const ADMIN_TOKEN = process.env.ADMIN_API_TOKEN ?? '';

async function getJson<T>(url: string, headers: Record<string, string>): Promise<T | null> {
  try {
    const res = await fetch(url, { headers, cache: 'no-store' });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/** Read a core-engine endpoint, attaching the admin token when configured. */
export function coreGet<T>(path: string): Promise<T | null> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (ADMIN_TOKEN) headers.Authorization = `Bearer ${ADMIN_TOKEN}`;
  return getJson<T>(`${CORE_API}${path}`, headers);
}

/** Read an analytics-engine (ML) endpoint with the internal service key. */
export function mlGet<T>(path: string): Promise<T | null> {
  return getJson<T>(`${ML_API}${path}`, { 'X-API-Key': ML_KEY });
}

/** Pull `results` out of a DRF page, or treat the body as a bare list. */
export function asList<T>(data: unknown): T[] {
  if (data && typeof data === 'object' && Array.isArray((data as { results?: T[] }).results)) {
    return (data as { results: T[] }).results;
  }
  if (Array.isArray(data)) return data as T[];
  return [];
}
