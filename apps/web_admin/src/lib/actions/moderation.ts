'use server';

/**
 * Server Actions for scam-report moderation.
 *
 * The core-engine has exposed `verify` and `dismiss` on the scam-report viewset
 * since sprint 4, but nothing called them — moderation was listed as a deferred
 * "could-have". These wire the existing endpoints to the dashboard, so a
 * flagged report can actually be actioned.
 *
 * Running as Server Actions keeps the staff token on the server: the browser
 * posts to Next, Next posts to Django. `revalidatePath` then refreshes the
 * table so the moderator sees the new status without a manual reload.
 */

import { revalidatePath } from 'next/cache';

import { corePost } from '@/lib/api/server';

export interface ModerationResult {
  ok: boolean;
  message: string;
}

async function moderate(id: number, verb: 'verify' | 'dismiss'): Promise<ModerationResult> {
  const result = await corePost<{ status?: string }>(`/trust/scam-reports/${id}/${verb}/`);

  if (!result.ok) {
    return { ok: false, message: result.error };
  }

  revalidatePath('/scam-reports');
  revalidatePath('/dashboard');
  return {
    ok: true,
    message: verb === 'verify' ? `Report #${id} marked as verified.` : `Report #${id} dismissed.`,
  };
}

export async function verifyScamReport(id: number): Promise<ModerationResult> {
  return moderate(id, 'verify');
}

export async function dismissScamReport(id: number): Promise<ModerationResult> {
  return moderate(id, 'dismiss');
}
