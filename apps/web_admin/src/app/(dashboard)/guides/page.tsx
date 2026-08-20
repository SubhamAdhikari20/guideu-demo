import { BadgeCheck, BadgeX } from 'lucide-react';

import { AdminTable } from '@/components/common/admin-table';
import { PageHeader } from '@/components/layout/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { verifyGuideAction } from '@/lib/actions/platform';
import { asList, coreGet } from '@/lib/api/server';

export const dynamic = 'force-dynamic';
interface GuideRow { id: number; email: string; first_name: string; last_name: string; is_guide_verified: boolean; guide_profile?: { license_number?: string; availability: string; service_areas?: string[] } }

export default async function GuidesPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const guides = asList<GuideRow>(await coreGet('/auth/users/?role=GUIDE&page_size=100')).filter((user) => Boolean(user.guide_profile));
  const { error } = await searchParams;
  return <div>
    <PageHeader title="Guide verification" subtitle="Review registered guide accounts, licence references, and live availability." />
    {error && <p className="bg-destructive/10 text-destructive mb-4 rounded-md p-3 text-sm">{error}</p>}
    <AdminTable columns={[{ key: 'guide', label: 'Guide' }, { key: 'licence', label: 'Licence' }, { key: 'availability', label: 'Availability' }, { key: 'verification', label: 'Verification' }, { key: 'actions', label: '' }]}
      rows={guides.map((guide) => ({
        id: guide.id,
        guide: <div><p className="font-medium">{`${guide.first_name} ${guide.last_name}`.trim()}</p><p className="text-muted-foreground text-xs">{guide.email}</p></div>,
        licence: guide.guide_profile?.license_number || 'Missing',
        availability: <Badge variant="outline">{guide.guide_profile?.availability ?? 'OFFLINE'}</Badge>,
        verification: <Badge variant={guide.is_guide_verified ? 'default' : 'secondary'}>{guide.is_guide_verified ? 'Verified' : 'Pending'}</Badge>,
        actions: <form action={verifyGuideAction}><input type="hidden" name="id" value={guide.id} /><input type="hidden" name="verified" value={String(!guide.is_guide_verified)} /><Button size="sm" variant={guide.is_guide_verified ? 'outline' : 'default'}>{guide.is_guide_verified ? <BadgeX className="size-3" /> : <BadgeCheck className="size-3" />}{guide.is_guide_verified ? 'Revoke' : 'Verify'}</Button></form>,
      }))} />
  </div>;
}
