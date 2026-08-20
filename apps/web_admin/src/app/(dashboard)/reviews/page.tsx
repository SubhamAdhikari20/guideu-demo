import { Check, X } from 'lucide-react';

import { AdminTable } from '@/components/common/admin-table';
import { PageHeader } from '@/components/layout/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { moderateReviewAction } from '@/lib/actions/platform';
import { asList, coreGet } from '@/lib/api/server';

export const dynamic = 'force-dynamic';
interface ReviewRow { id: number; author: number; target_kind: string; rating: number; title: string; comment: string; status: string; is_flagged: boolean; created_at: string }

export default async function ReviewsPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const reviews = asList<ReviewRow>(await coreGet('/reviews/reviews/?page_size=100'));
  const { error } = await searchParams;
  return <div><PageHeader title="Review moderation" subtitle="Approve authentic traveller feedback and reject abusive or misleading content." />
    {error && <p className="bg-destructive/10 text-destructive mb-4 rounded-md p-3 text-sm">{error}</p>}
    <AdminTable columns={[{ key: 'review', label: 'Review' }, { key: 'rating', label: 'Rating' }, { key: 'target', label: 'Target' }, { key: 'status', label: 'Status' }, { key: 'actions', label: '' }]}
      rows={reviews.map((review) => ({
        id: review.id,
        review: <div className="max-w-lg"><p className="font-medium">{review.title || 'Untitled review'}</p><p className="text-muted-foreground line-clamp-2 text-xs">{review.comment}</p></div>,
        rating: `${review.rating} / 5`,
        target: review.target_kind,
        status: <Badge variant={review.is_flagged ? 'destructive' : 'secondary'}>{review.status}{review.is_flagged ? ' • flagged' : ''}</Badge>,
        actions: <div className="flex gap-2"><form action={moderateReviewAction}><input type="hidden" name="id" value={review.id} /><input type="hidden" name="status" value="APPROVED" /><Button size="sm" variant="outline"><Check className="size-3" /> Approve</Button></form><form action={moderateReviewAction}><input type="hidden" name="id" value={review.id} /><input type="hidden" name="status" value="REJECTED" /><Button size="sm" variant="outline"><X className="size-3" /> Reject</Button></form></div>,
      }))} />
  </div>;
}
