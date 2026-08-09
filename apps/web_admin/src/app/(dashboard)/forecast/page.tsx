import { EmptyState, PageHeader, Panel, StatCard } from '@/components/ui/card';
import { ForecastChart, type ForecastPoint } from '@/components/ui/forecast-chart';
import { mlPost } from '@/lib/api/server';

interface ForecastResponse {
  model_version: string;
  year: number | null;
  region: string | null;
  expected_error_pct: number | null;
  peak_month: number | null;
  items: ForecastPoint[];
  note: string | null;
}

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

export const dynamic = 'force-dynamic';

export default async function ForecastPage() {
  const forecast = await mlPost<ForecastResponse>('/api/v1/forecast/arrivals', {});
  const items = forecast?.items ?? [];
  const total = items.reduce((sum, p) => sum + p.predicted_arrivals, 0);

  return (
    <div>
      <PageHeader
        title="Demand Forecast"
        subtitle="Projected monthly tourist arrivals, used to plan guide capacity ahead of each season."
      />

      {items.length === 0 ? (
        <Panel title="Forecast">
          <EmptyState>
            No forecast available. Train the arrivals model
            (<code>python -m training.run_all</code>) and check that the
            analytics-engine is reachable.
          </EmptyState>
        </Panel>
      ) : (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-3">
            <StatCard label={`Forecast total for ${forecast?.year}`} value={total.toLocaleString()} />
            <StatCard
              label="Busiest month"
              value={forecast?.peak_month ? MONTH_NAMES[forecast.peak_month - 1] : '—'}
            />
            <StatCard
              label="Typical error"
              value={forecast?.expected_error_pct ? `±${forecast.expected_error_pct}%` : '—'}
            />
          </div>

          <Panel title={`Monthly arrivals — ${forecast?.year}`}>
            <ForecastChart points={items} />
            {forecast?.note && (
              <p className="mt-4 border-t border-zinc-100 pt-3 text-xs text-zinc-500 dark:border-zinc-900">
                {forecast.note} Model: <code>{forecast.model_version}</code>
              </p>
            )}
          </Panel>
        </>
      )}
    </div>
  );
}
