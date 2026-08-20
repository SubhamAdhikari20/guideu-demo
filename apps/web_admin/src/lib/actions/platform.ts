'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';

import { corePost } from '@/lib/api/server';

function resultPath(path: string, ok: boolean, error?: string): never {
  const query = ok ? 'updated=1' : `error=${encodeURIComponent(error ?? 'Update failed')}`;
  redirect(`${path}?${query}`);
}

export async function verifyGuideAction(formData: FormData) {
  const id = Number(formData.get('id'));
  const verified = formData.get('verified') === 'true';
  const result = await corePost(`/auth/users/${id}/verify-guide/`, { verified });
  revalidatePath('/guides');
  resultPath('/guides', result.ok, result.ok ? undefined : result.error);
}

export async function suspendUserAction(formData: FormData) {
  const id = Number(formData.get('id'));
  const active = formData.get('active') === 'true';
  const result = await corePost(`/auth/users/${id}/suspend/`, { active });
  revalidatePath('/users');
  resultPath('/users', result.ok, result.ok ? undefined : result.error);
}

export async function resolveSosAction(formData: FormData) {
  const id = Number(formData.get('id'));
  const result = await corePost(`/safety/sos/${id}/resolve/`);
  revalidatePath('/safety');
  resultPath('/safety', result.ok, result.ok ? undefined : result.error);
}

export async function moderateReviewAction(formData: FormData) {
  const id = Number(formData.get('id'));
  const status = String(formData.get('status'));
  const result = await corePost(`/reviews/reviews/${id}/moderate/`, { status });
  revalidatePath('/reviews');
  resultPath('/reviews', result.ok, result.ok ? undefined : result.error);
}

export async function createOfferingAction(formData: FormData) {
  const serviceType = String(formData.get('service_type'));
  const capacity = Number(formData.get('capacity'));
  const body = {
    service_type: serviceType,
    provider_name: String(formData.get('provider_name')),
    title: String(formData.get('title')),
    location: String(formData.get('location') ?? ''),
    origin: String(formData.get('origin') ?? ''),
    destination: String(formData.get('destination') ?? ''),
    unit_price: String(formData.get('unit_price')),
    capacity,
    available_units: capacity,
    currency: 'NPR',
    amenities: [],
    metadata: {},
  };
  const result = await corePost('/bookings/travel-offerings/', body);
  revalidatePath('/inventory');
  resultPath('/inventory', result.ok, result.ok ? undefined : result.error);
}
