import { Info } from 'lucide-react';

import { PageHeader } from '@/components/layout/page-header';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { asList, coreGet, hasAdminToken } from '@/lib/api/server';

import { ReportRowActions } from './report-row-actions';
import type { ScamReport } from './types';

export const dynamic = 'force-dynamic';

const SEVERITY_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  'Likely Scam': 'destructive',
  'Severe Overcharge': 'destructive',
  'Moderate Overcharge': 'default',
  'Mild Overcharge': 'secondary',
  Fair: 'outline',
};

const STATUS_VARIANT: Record<string, 'default' | 'secondary' | 'outline'> = {
  VERIFIED: 'default',
  SUBMITTED: 'secondary',
  DISMISSED: 'outline',
};

export default async function ScamReportsPage() {
  const page = await coreGet<unknown>('/trust/scam-reports/?ordering=-created_at&page_size=50');
  const reports = asList<ScamReport>(page);

  const pending = reports.filter((r) => r.status === 'SUBMITTED').length;

  return (
    <div>
      <PageHeader
        title="Scam reports"
        subtitle="Tourist-submitted overcharge reports, scored by the anti-scam model and awaiting review."
        actions={
          <Badge variant={pending > 0 ? 'default' : 'secondary'} className="tabular-nums">
            {pending} awaiting review
          </Badge>
        }
      />

      {!hasAdminToken && (
        <Card className="border-amber-500/40 bg-amber-500/5 mb-4">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Info className="size-4" /> Read-only mode
            </CardTitle>
            <CardDescription>
              No staff token is configured, so moderation actions are disabled. Set{' '}
              <code className="bg-muted rounded px-1 py-0.5 text-xs">ADMIN_API_TOKEN</code> to an
              admin JWT to verify or dismiss reports.
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Reports</CardTitle>
          <CardDescription>
            The ratio compares the quoted price against the fair benchmark for that service,
            region and season. Anything above 1.25× is flagged automatically.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {reports.length === 0 ? (
            <p className="text-muted-foreground rounded-lg border border-dashed p-8 text-center text-sm">
              {hasAdminToken
                ? 'No scam reports have been submitted yet.'
                : 'No reports could be read. This endpoint needs a staff token.'}
            </p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-14">#</TableHead>
                    <TableHead>Service</TableHead>
                    <TableHead>Region</TableHead>
                    <TableHead className="text-right">Quoted</TableHead>
                    <TableHead className="text-right">Ratio</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-10" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reports.map((report) => (
                    <TableRow key={report.id}>
                      <TableCell className="text-muted-foreground tabular-nums">
                        {report.id}
                      </TableCell>
                      <TableCell className="font-medium">{report.service_type}</TableCell>
                      <TableCell className="text-muted-foreground">{report.region}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        {report.quoted_price_npr.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        <Tooltip>
                          <TooltipTrigger
                            render={
                              <span className={report.was_flagged_by_app ? 'font-semibold' : ''}>
                                {report.overcharge_ratio}×
                              </span>
                            }
                          />
                          <TooltipContent>
                            Benchmark {report.benchmark_price_npr?.toLocaleString() ?? '—'} NPR
                          </TooltipContent>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Badge variant={SEVERITY_VARIANT[report.scam_severity] ?? 'secondary'}>
                          {report.scam_severity}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={STATUS_VARIANT[report.status] ?? 'secondary'}>
                          {report.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <ReportRowActions report={report} canModerate={hasAdminToken} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
