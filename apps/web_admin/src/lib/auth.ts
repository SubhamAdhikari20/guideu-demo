import 'server-only';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

const CORE_API = process.env.CORE_API_BASE_URL ?? 'http://localhost:8000/api/v1';
export const ACCESS_COOKIE = 'guideu_admin_access';
export const REFRESH_COOKIE = 'guideu_admin_refresh';

export interface AdminUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
}

export async function currentAdmin(): Promise<AdminUser | null> {
  const cookieStore = await cookies();
  let access = cookieStore.get(ACCESS_COOKIE)?.value;
  const refresh = cookieStore.get(REFRESH_COOKIE)?.value;
  if (!access && !refresh) return null;
  try {
    let response = await fetch(`${CORE_API}/auth/users/me/`, {
      headers: { Authorization: `Bearer ${access}` },
      cache: 'no-store',
    });
    if (!response.ok && refresh) {
      const refreshed = await fetch(`${CORE_API}/auth/token/refresh/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }), cache: 'no-store',
      });
      if (refreshed.ok) {
        access = ((await refreshed.json()) as { access?: string }).access;
        response = await fetch(`${CORE_API}/auth/users/me/`, {
          headers: { Authorization: `Bearer ${access}` }, cache: 'no-store',
        });
      }
    }
    if (!response.ok) return null;
    const user = (await response.json()) as AdminUser;
    return user.role === 'ADMIN' ? user : null;
  } catch {
    return null;
  }
}

export async function requireAdmin(): Promise<AdminUser> {
  const user = await currentAdmin();
  if (!user) redirect('/login');
  return user;
}
