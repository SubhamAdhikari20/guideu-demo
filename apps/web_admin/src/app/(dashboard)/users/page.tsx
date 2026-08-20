import { Ban, Users } from 'lucide-react';

import { AdminTable } from '@/components/common/admin-table';
import { PageHeader } from '@/components/layout/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { asList, coreGet } from '@/lib/api/server';
import { suspendUserAction } from '@/lib/actions/platform';

export const dynamic = 'force-dynamic';
interface UserRow { id: number; email: string; username: string; first_name: string; last_name: string; role: string; phone_number?: string; is_guide_verified: boolean; is_active: boolean; created_at: string }

export default async function UsersPage({ searchParams }: { searchParams: Promise<{ error?: string; updated?: string }> }) {
  const users = asList<UserRow>(await coreGet('/auth/users/?page_size=100'));
  const notice = await searchParams;
  return <div>
    <PageHeader title="Users" subtitle="Tourist, guide, and administrator accounts with role-aware controls." />
    {notice.error && <p className="bg-destructive/10 text-destructive mb-4 rounded-md p-3 text-sm">{notice.error}</p>}
    <AdminTable
      columns={[{ key: 'user', label: 'User' }, { key: 'role', label: 'Role' }, { key: 'phone', label: 'Phone' }, { key: 'joined', label: 'Joined' }, { key: 'actions', label: '' }]}
      rows={users.map((user) => ({
        id: user.id,
        user: <div><p className="font-medium">{`${user.first_name} ${user.last_name}`.trim() || user.username}</p><p className="text-muted-foreground text-xs">{user.email}</p></div>,
        role: <Badge variant="secondary">{user.role}</Badge>,
        phone: user.phone_number || '—',
        joined: new Date(user.created_at).toLocaleDateString(),
        actions: user.role !== 'ADMIN' ? <form action={suspendUserAction}><input type="hidden" name="id" value={user.id} /><input type="hidden" name="active" value={String(!user.is_active)} /><Button size="sm" variant="outline"><Ban className="size-3" /> {user.is_active ? 'Suspend' : 'Activate'}</Button></form> : <Users className="text-muted-foreground size-4" />,
      }))}
    />
  </div>;
}
