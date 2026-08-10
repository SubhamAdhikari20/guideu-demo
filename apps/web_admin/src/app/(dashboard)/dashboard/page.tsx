import { BrainCircuit, CalendarDays, MountainSnow, ShieldAlert, Users } from 'lucide-react';
import Link from 'next/link';
import type { ReactNode } from 'react';

import { PageHeader } from '@/components/layout/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { coreGet, mlGet } from '@/lib/api/server';

export const dynamic = 'force-dynamic';

interface ModelCard {
  name: string;
  version: string;
  metrics: Record<string, number>;
  notes: string;
}

async function count(path: string): Promise<number | null> {
  const data = await coreGet<{ count?: number }>(path);
  return data?.count ?? null;
}

function fmt(value: number | null): string {
  return value === null ? '—' : value.toLocaleString();
}

function StatCard({
  label,
  value,
  icon,
  hint,
}: {
  label: string;
  value: string;
  icon: ReactNode;
  hint: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-3xl tabular-nums">{value}</CardTitle>
        <CardAction className="text-muted-foreground">{icon}</CardAction>
      </CardHeader>
      <CardFooter>
        <p className="text-muted-foreground text-xs">{hint}</p>
      </CardFooter>
    </Card>
  );
}

const HEADLINES: Record<string, { metric: string; label: string; good: string }> = {
  scam_classifier: { metric: 'f1', label: 'F1 score', good: 'vs 0.000 for the majority baseline' },
  route_recommender: {
    metric: 'model_only_lift_over_popularity',
    label: 'Lift over popularity',
    good: 'hit-rate@10 against a non-personalised baseline',
  },
  guide_ranker: { metric: 'rmse', label: 'RMSE', good: 'vs 0.688 for predicting the mean' },
  arrivals_forecaster: { metric: 'mape', label: 'MAPE %', good: 'vs 38.6% for a seasonal naive forecast' },
  tourist_segments: { metric: 'silhouette', label: 'Silhouette', good: 'weak by design — reported honestly' },
};

export default async function DashboardPage() {
  const [models, guides, routes, events, benchmarks, reports] = await Promise.all([
    mlGet<ModelCard[]>('/api/v1/models'),
    count('/catalog/guides-registry/?page_size=1'),
    count('/catalog/routes/?page_size=1'),
    count('/catalog/events/?page_size=1'),
    count('/catalog/pricing-benchmarks/?page_size=1'),
    count('/trust/scam-reports/?page_size=1'),
  ]);

  return (
    <div>
      <PageHeader
        title="Overview"
        subtitle="Catalog health and machine-learning status across the GuideU platform."
        actions={
          <Button variant="outline" render={<Link href="/models" />}>
            <BrainCircuit className="size-4" />
            Model registry
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Verified guides"
          value={fmt(guides)}
          icon={<Users className="size-4" />}
          hint="Active NTB / IFMGA registry entries"
        />
        <StatCard
          label="Trekking routes"
          value={fmt(routes)}
          icon={<MountainSnow className="size-4" />}
          hint="26 base treks across 375 named variants"
        />
        <StatCard
          label="Festivals"
          value={fmt(events)}
          icon={<CalendarDays className="size-4" />}
          hint="Cultural calendar used for discovery"
        />
        <StatCard
          label="Price benchmarks"
          value={fmt(benchmarks)}
          icon={<ShieldAlert className="size-4" />}
          hint="Fair-price rows behind every scam check"
        />
      </div>

      <Tabs defaultValue="models" className="mt-6">
        <TabsList>
          <TabsTrigger value="models">Machine learning</TabsTrigger>
          <TabsTrigger value="trust">Trust &amp; safety</TabsTrigger>
        </TabsList>

        <TabsContent value="models">
          <Card>
            <CardHeader>
              <CardTitle>Registered models</CardTitle>
              <CardDescription>
                {models?.length
                  ? `${models.length} models loaded from the analytics-engine registry.`
                  : 'The analytics-engine is not reachable, so no models could be listed.'}
              </CardDescription>
              <CardAction>
                <Button variant="ghost" size="sm" render={<Link href="/models" />}>
                  View all
                </Button>
              </CardAction>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {(models ?? []).map((model) => {
                const headline = HEADLINES[model.name];
                const value = headline ? model.metrics?.[headline.metric] : undefined;
                return (
                  <div key={model.name} className="rounded-lg border p-4">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-mono text-sm font-medium">{model.name}</p>
                      <Popover>
                        <PopoverTrigger
                          render={
                            <Badge variant="secondary" className="cursor-help tabular-nums">
                              {value !== undefined ? value : '—'}
                            </Badge>
                          }
                        />
                        <PopoverContent className="w-72 text-sm">
                          <p className="font-medium">{headline?.label ?? 'Metric'}</p>
                          <p className="text-muted-foreground mt-1 text-xs">{headline?.good}</p>
                        </PopoverContent>
                      </Popover>
                    </div>
                    <p className="text-muted-foreground mt-2 line-clamp-3 text-xs">{model.notes}</p>
                  </div>
                );
              })}
              {!models?.length && (
                <p className="text-muted-foreground col-span-full rounded-lg border border-dashed p-6 text-center text-sm">
                  Start the analytics-engine and run{' '}
                  <code className="bg-muted rounded px-1 py-0.5">python -m training.run_all</code>.
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trust">
          <Card>
            <CardHeader>
              <CardTitle>Scam reports</CardTitle>
              <CardDescription>
                Tourist-submitted overcharge reports awaiting moderator review.
              </CardDescription>
              <CardAction>
                <Button variant="ghost" size="sm" render={<Link href="/scam-reports" />}>
                  Moderate
                </Button>
              </CardAction>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-semibold tabular-nums">{fmt(reports)}</p>
              <p className="text-muted-foreground mt-1 text-sm">
                {reports === null
                  ? 'Needs a staff token (ADMIN_API_TOKEN) to read.'
                  : 'Reports visible to this staff account.'}
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
