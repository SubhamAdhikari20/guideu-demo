'use client';

import { Check, Eye, MoreHorizontal, X } from 'lucide-react';
import { useState, useTransition } from 'react';
import { toast } from 'sonner';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Separator } from '@/components/ui/separator';
import { dismissScamReport, verifyScamReport } from '@/lib/actions/moderation';

import type { ScamReport } from './types';

type PendingAction = 'verify' | 'dismiss' | null;

export function ReportRowActions({
  report,
  canModerate,
}: {
  report: ScamReport;
  canModerate: boolean;
}) {
  const [confirming, setConfirming] = useState<PendingAction>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [isPending, startTransition] = useTransition();

  const run = (action: Exclude<PendingAction, null>) => {
    startTransition(async () => {
      const result =
        action === 'verify'
          ? await verifyScamReport(report.id)
          : await dismissScamReport(report.id);

      if (result.ok) {
        toast.success(result.message);
      } else {
        // A failed moderation must be loud: the row will not have changed, and a
        // silent failure would leave the moderator believing it had.
        toast.error('Could not update the report', { description: result.message });
      }
      setConfirming(null);
    });
  };

  const alreadyHandled = report.status !== 'SUBMITTED';

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <Button variant="ghost" size="icon-sm" aria-label={`Actions for report ${report.id}`}>
              <MoreHorizontal className="size-4" />
            </Button>
          }
        />
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>Report #{report.id}</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setDetailOpen(true)}>
            <Eye className="size-4" /> View details
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            disabled={!canModerate || alreadyHandled || isPending}
            onClick={() => setConfirming('verify')}
          >
            <Check className="size-4" /> Mark as verified
          </DropdownMenuItem>
          <DropdownMenuItem
            variant="destructive"
            disabled={!canModerate || alreadyHandled || isPending}
            onClick={() => setConfirming('dismiss')}
          >
            <X className="size-4" /> Dismiss report
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Moderation changes a provider's standing, so it is confirmed rather than
          fired straight from the menu. */}
      <AlertDialog open={confirming !== null} onOpenChange={(open) => !open && setConfirming(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {confirming === 'verify' ? 'Mark this report as verified?' : 'Dismiss this report?'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {confirming === 'verify' ? (
                <>
                  Report #{report.id} covers a {report.service_type} quoted at{' '}
                  {report.quoted_price_npr.toLocaleString()} NPR, which is{' '}
                  {report.overcharge_ratio}× the fair benchmark. Verifying records that a
                  moderator confirmed the overcharge.
                </>
              ) : (
                <>
                  Dismissing marks report #{report.id} as not a genuine overcharge. The
                  tourist&apos;s submission is kept, but it stops counting against the provider.
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              disabled={isPending}
              onClick={(event) => {
                event.preventDefault();
                if (confirming) run(confirming);
              }}
            >
              {isPending ? 'Working…' : confirming === 'verify' ? 'Verify' : 'Dismiss'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Report #{report.id}</DialogTitle>
            <DialogDescription>
              {report.service_type} in {report.region}
              {report.season ? ` · ${report.season}` : ''}
            </DialogDescription>
          </DialogHeader>

          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-muted-foreground text-xs">Quoted</dt>
              <dd className="font-semibold tabular-nums">
                {report.quoted_price_npr.toLocaleString()} NPR
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground text-xs">Fair benchmark</dt>
              <dd className="font-semibold tabular-nums">
                {report.benchmark_price_npr?.toLocaleString() ?? '—'} NPR
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground text-xs">Overcharge ratio</dt>
              <dd className="font-semibold tabular-nums">{report.overcharge_ratio}×</dd>
            </div>
            <div>
              <dt className="text-muted-foreground text-xs">Model probability</dt>
              <dd className="font-semibold tabular-nums">
                {report.ml_scam_probability ?? '—'}
              </dd>
            </div>
          </dl>

          {report.description && (
            <>
              <Separator />
              <p className="text-sm leading-relaxed">{report.description}</p>
            </>
          )}

          <div className="flex flex-wrap gap-1.5">
            <Badge variant="outline">{report.scam_severity}</Badge>
            <Badge variant={report.status === 'VERIFIED' ? 'default' : 'secondary'}>
              {report.status}
            </Badge>
            {report.verified_by_moderator && <Badge variant="outline">Moderator confirmed</Badge>}
          </div>

          <DialogFooter>
            <DialogClose render={<Button variant="outline">Close</Button>} />
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
