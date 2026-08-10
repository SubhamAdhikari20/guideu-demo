import { Info } from 'lucide-react';
import { Suspense } from 'react';

import { PageHeader } from '@/components/layout/page-header';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { ForecastChart, type ForecastPoint } from '@/components/ui/forecast-chart';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { mlGet, mlPost } from '@/lib/api/server';

import { ForecastControls } from './forecast-controls';

interface ForecastResponse {
  model_version: string;
  year: number | null;
  region: string | null;
  expected_error_pct: number | null;
  peak_month: number | null;
  items: ForecastPoint[];
  last_observed_year: number | null;
  horizon_years: number | null;
  reliable: boolean;
  note: string | null;
}

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

export const dynamic = 'force-dynamic';

export default async function ForecastPage({
  searchParams,
}: {
  searchParams: Promise<{ year?: string; region?: string }>;
}) {
  const params = await searchParams;
  const region = params.region ?? '';

  // Default to the first year past the training data rather than "this year":
  // the trend compounds, so a default of the current calendar year silently
  // shows a wildly over-projected number whenever the data is a season behind.
  const requested = Number(params.year) || undefined;
  const probe = requested
    ? null
    : await mlPost<ForecastResponse>('/api/v1/forecast/arrivals', { year: null, region: null });
  const year = requested ?? (probe?.year || new Date().getFullYear());

  const [forecast, regions] = await Promise.all([
    mlPost<ForecastResponse>('/api/v1/forecast/arrivals', { year, region: region || null }),
    mlGet<string[]>('/api/v1/forecast/regions'),
  ]);

  const items = forecast?.items ?? [];
  const total = items.reduce((sum, p) => sum + p.predicted_arrivals, 0);

  return (
    <div>
      <PageHeader
        title="Demand forecast"
        subtitle="Projected monthly tourist arrivals, used to plan guide capacity ahead of each season."
      />

      <Card className="mb-4">
        <CardContent className="pt-6">
          <Suspense fallback={<Skeleton className="h-16 w-full" />}>
            <ForecastControls
              year={year}
              region={region}
              regions={regions ?? []}
              lastObservedYear={forecast?.last_observed_year ?? null}
            />
          </Suspense>
        </CardContent>
      </Card>

      {forecast && !forecast.reliable && (
        <Card className="border-amber-500/40 bg-amber-500/5 mb-4">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Info className="size-4" /> Beyond the model&apos;s useful horizon
            </CardTitle>
            <CardDescription>
              This is {forecast.horizon_years} years past the last observed year (
              {forecast.last_observed_year}). The trend compounds a post-COVID recovery rate, so
              these figures overstate demand badly — forecast{' '}
              {(forecast.last_observed_year ?? 0) + 1} for a number worth planning against.
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {items.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground rounded-lg border border-dashed p-8 text-center text-sm">
              No forecast available. Train the arrivals model with{' '}
              <code className="bg-muted rounded px-1 py-0.5 text-xs">
                python -m training.run_all
              </code>{' '}
              and check that the analytics-engine is reachable.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="mb-4 grid gap-4 sm:grid-cols-3">
            <Card>
              <CardHeader>
                <CardDescription>Forecast total for {forecast?.year}</CardDescription>
                <CardTitle className="text-3xl tabular-nums">{total.toLocaleString()}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardDescription>Busiest month</CardDescription>
                <CardTitle className="text-3xl">
                  {forecast?.peak_month ? MONTH_NAMES[forecast.peak_month - 1] : '—'}
                </CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardDescription>Typical error</CardDescription>
                <CardTitle className="text-3xl tabular-nums">
                  ±{forecast?.expected_error_pct ?? '—'}%
                </CardTitle>
                <CardAction>
                  <Popover>
                    <PopoverTrigger
                      render={
                        <Badge variant="outline" className="cursor-help gap-1">
                          <Info className="size-3" /> Why
                        </Badge>
                      }
                    />
                    <PopoverContent className="w-80 text-sm">
                      <p className="font-medium">Read the band, not the point</p>
                      <p className="text-muted-foreground mt-1 text-xs leading-relaxed">
                        Mean absolute percentage error on the held-out 2024 year. The model was
                        fitted on three years of post-COVID recovery, and on the 2023 validation
                        year a seasonal naive forecast beats it — so the range is the forecast,
                        not the single number.
                      </p>
                    </PopoverContent>
                  </Popover>
                </CardAction>
              </CardHeader>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>
                Monthly arrivals — {forecast?.year}
                {forecast?.region ? ` · ${forecast.region}` : ''}
              </CardTitle>
              <CardDescription>
                The shaded band is the model&apos;s expected error range.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="chart">
                <TabsList>
                  <TabsTrigger value="chart">Chart</TabsTrigger>
                  <TabsTrigger value="table">Table</TabsTrigger>
                </TabsList>
                <TabsContent value="chart">
                  <ForecastChart points={items} />
                </TabsContent>
                <TabsContent value="table">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Month</TableHead>
                        <TableHead className="text-right">Forecast</TableHead>
                        <TableHead className="text-right">Likely range</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {items.map((point) => (
                        <TableRow key={point.month}>
                          <TableCell>{MONTH_NAMES[point.month - 1]}</TableCell>
                          <TableCell className="text-right font-medium tabular-nums">
                            {point.predicted_arrivals.toLocaleString()}
                          </TableCell>
                          <TableCell className="text-muted-foreground text-right tabular-nums">
                            {point.lower_estimate.toLocaleString()} –{' '}
                            {point.upper_estimate.toLocaleString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TabsContent>
              </Tabs>
            </CardContent>
            {forecast?.note && (
              <CardFooter>
                <p className="text-muted-foreground text-xs">
                  {forecast.note} Model: <code>{forecast.model_version}</code>
                </p>
              </CardFooter>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
