import { PageHeader, Panel, StatCard } from '@/components/ui/card';
import { coreGet, mlGet } from '@/lib/api/server';

export const dynamic = 'force-dynamic';

interface Page {
  count?: number;
}

async function count(path: string): Promise<number | string> {
  const data = await coreGet<Page>(path);
  return data?.count ?? '—';
}

export default async function DashboardPage() {
  const [models, guides, routes, events] = await Promise.all([
    mlGet<unknown[]>('/api/v1/models'),
    count('/catalog/guides-registry/?page_size=1'),
    count('/catalog/routes/?page_size=1'),
    count('/catalog/events/?page_size=1'),
  ]);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="A quick view of the GuideU platform — models, guides, routes and events."
      />
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="ML models" value={models?.length ?? '—'} />
        <StatCard label="Verified guides" value={guides} />
        <StatCard label="Trekking routes" value={routes} />
        <StatCard label="Festivals" value={events} />
      </div>
      <Panel title="About this dashboard">
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          The admin panel reads the ML model registry from the analytics-engine and
          the catalog from the core-engine. Scam-report moderation needs a staff
          token (ADMIN_API_TOKEN). Counts come from the public catalog endpoints.
        </p>
      </Panel>
    </div>
  );
}
