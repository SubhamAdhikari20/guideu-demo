import { CheckCircle2, MapPin } from 'lucide-react';

import { AdminTable } from '@/components/common/admin-table';
import { PageHeader } from '@/components/layout/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { resolveSosAction } from '@/lib/actions/platform';
import { asList, coreGet } from '@/lib/api/server';

export const dynamic = 'force-dynamic';
interface SosRow { id: number; user: number; latitude?: string; longitude?: string; message: string; source: string; status: string; created_at: string }

export default async function SafetyPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const alerts = asList<SosRow>(await coreGet('/safety/sos/?page_size=100'));
  const { error } = await searchParams;
  return <div><PageHeader title="Safety response" subtitle="Live SOS queue from travellers and registered trekking devices." />
    {error && <p className="bg-destructive/10 text-destructive mb-4 rounded-md p-3 text-sm">{error}</p>}
    <AdminTable columns={[{ key: 'alert', label: 'Alert' }, { key: 'source', label: 'Source' }, { key: 'location', label: 'Last location' }, { key: 'status', label: 'Status' }, { key: 'created', label: 'Raised' }, { key: 'actions', label: '' }]}
      rows={alerts.map((alert) => ({
        id: alert.id,
        alert: <div><p className="font-medium">User #{alert.user}</p><p className="text-muted-foreground max-w-sm text-xs">{alert.message || 'Emergency assistance requested'}</p></div>,
        source: alert.source,
        location: alert.latitude && alert.longitude ? <span className="flex items-center gap-1"><MapPin className="size-3" />{alert.latitude}, {alert.longitude}</span> : 'Unavailable',
        status: <Badge variant={alert.status === 'ACTIVE' ? 'destructive' : 'secondary'}>{alert.status}</Badge>,
        created: new Date(alert.created_at).toLocaleString(),
        actions: alert.status === 'ACTIVE' ? <form action={resolveSosAction}><input type="hidden" name="id" value={alert.id} /><Button size="sm"><CheckCircle2 className="size-3" /> Resolve</Button></form> : null,
      }))} />
  </div>;
}
