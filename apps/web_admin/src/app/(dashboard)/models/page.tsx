import { EmptyState, PageHeader, Panel } from '@/components/ui/card';
import { mlGet } from '@/lib/api/server';

interface ModelCard {
  name: string;
  version: string;
  metrics: Record<string, number>;
  params: Record<string, unknown>;
  trained_at: string | null;
  n_train: number | null;
  notes: string;
}

export const dynamic = 'force-dynamic';

export default async function ModelsPage() {
  const models = await mlGet<ModelCard[]>('/api/v1/models');

  return (
    <div>
      <PageHeader
        title="ML Models"
        subtitle="The analytics-engine model registry — versions, metrics and training metadata."
      />
      <Panel title="Registered models">
        {!models || models.length === 0 ? (
          <EmptyState>
            No models found. Start the analytics-engine and train the models, or
            check ANALYTICS_ENGINE_URL / ANALYTICS_API_KEY.
          </EmptyState>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-zinc-200 text-zinc-500 dark:border-zinc-800">
                <tr>
                  <th className="py-2 pr-4">Model</th>
                  <th className="py-2 pr-4">Version</th>
                  <th className="py-2 pr-4">Metrics</th>
                  <th className="py-2 pr-4">Trained on</th>
                  <th className="py-2">Notes</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => (
                  <tr key={`${m.name}-${m.version}`} className="border-b border-zinc-100 dark:border-zinc-900">
                    <td className="py-2 pr-4 font-medium">{m.name}</td>
                    <td className="py-2 pr-4">{m.version}</td>
                    <td className="py-2 pr-4">
                      {Object.entries(m.metrics ?? {})
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(', ') || '—'}
                    </td>
                    <td className="py-2 pr-4">{m.n_train ?? '—'}</td>
                    <td className="py-2 text-zinc-500">{m.notes || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
