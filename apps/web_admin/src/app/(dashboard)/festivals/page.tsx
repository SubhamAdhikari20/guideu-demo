import { EmptyState, PageHeader, Panel } from '@/components/ui/card';
import { coreGet } from '@/lib/api/server';

interface FestivalMonth {
  month: number;
  month_name: string;
  festivals: {
    festival_name: string;
    event_type: string;
    significance: string;
    duration_days: number;
    regions: string[];
  }[];
}

export const dynamic = 'force-dynamic';

export default async function FestivalsPage() {
  const data = await coreGet<{ months: FestivalMonth[] }>(
    '/catalog/events/upcoming/?months=12',
  );
  const months = (data?.months ?? []).filter((m) => m.festivals.length > 0);

  return (
    <div>
      <PageHeader
        title="Festivals & Events"
        subtitle="The information-hub calendar shown to travellers, grouped by month."
      />
      {months.length === 0 ? (
        <EmptyState>
          No festivals found. Seed the catalog (`manage.py seed_from_dataset`) to
          populate the calendar.
        </EmptyState>
      ) : (
        <div className="flex flex-col gap-4">
          {months.map((m) => (
            <Panel key={m.month} title={m.month_name}>
              <ul className="flex flex-col gap-2">
                {m.festivals.map((f) => (
                  <li
                    key={f.festival_name}
                    className="flex flex-wrap items-center gap-3 text-sm"
                  >
                    <span className="font-medium">{f.festival_name}</span>
                    <span className="rounded-full bg-[#138086]/10 px-2 py-0.5 text-xs text-[#138086]">
                      {f.event_type}
                    </span>
                    <span className="text-zinc-500">{f.duration_days} days</span>
                    <span className="text-zinc-500">
                      {f.regions.length > 0 ? f.regions.join(', ') : 'Across Nepal'}
                    </span>
                  </li>
                ))}
              </ul>
            </Panel>
          ))}
        </div>
      )}
    </div>
  );
}
