'use server';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { ACCESS_COOKIE, REFRESH_COOKIE } from '@/lib/auth';

const CORE_API = process.env.CORE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export async function loginAction(formData: FormData) {
  const email = String(formData.get('email') ?? '').trim().toLowerCase();
  const password = String(formData.get('password') ?? '');
  let error = '';
  let access = '';
  let refresh = '';

  if (!email || !password) {
    error = 'Enter your administrator email and password.';
  } else {
    try {
      const tokenResponse = await fetch(`${CORE_API}/auth/token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        cache: 'no-store',
      });
      if (tokenResponse.ok) {
        const tokens = (await tokenResponse.json()) as { access: string; refresh: string };
        const meResponse = await fetch(`${CORE_API}/auth/users/me/`, {
          headers: { Authorization: `Bearer ${tokens.access}` },
          cache: 'no-store',
        });
        const user = meResponse.ok ? ((await meResponse.json()) as { role?: string }) : null;
        if (user?.role === 'ADMIN') {
          access = tokens.access;
          refresh = tokens.refresh;
        } else {
          error = 'This account does not have administrator access.';
        }
      } else {
        error = 'Invalid email or password.';
      }
    } catch {
      error = 'The GuideU core service is unavailable.';
    }
  }

  if (error) redirect(`/login?error=${encodeURIComponent(error)}`);
  const cookieStore = await cookies();
  const secure = process.env.NODE_ENV === 'production';
  cookieStore.set(ACCESS_COOKIE, access, { httpOnly: true, secure, sameSite: 'lax', path: '/', maxAge: 60 * 60 });
  cookieStore.set(REFRESH_COOKIE, refresh, { httpOnly: true, secure, sameSite: 'lax', path: '/', maxAge: 60 * 60 * 24 * 7 });
  redirect('/dashboard');
}

export async function logoutAction() {
  const cookieStore = await cookies();
  cookieStore.delete(ACCESS_COOKIE);
  cookieStore.delete(REFRESH_COOKIE);
  redirect('/login');
}
