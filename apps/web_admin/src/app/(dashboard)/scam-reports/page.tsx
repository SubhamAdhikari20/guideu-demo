import { EmptyState, PageHeader, Panel } from '@/components/ui/card';
import { asList, coreGet } from '@/lib/api/server';

interface ScamReport {
  id: number;
  service_type: string;
  region: string;
  quoted_price_npr: number;
  benchmark_price_npr: number | null;
  overcharge_ratio: number | null;
  scam_severity: string;
  status: string;
  created_at: string;
}

export const dynamic = 'force-dynamic';

function severityColor(severity: string): string {
  switch (severity) {
    case 'High':
      return 'bg-red-100 text-red-700';
    case 'Medium':
      return 'bg-amber-100 text-amber-700';
    default:
      return 'bg-zinc-100 text-zinc-600';
  }
}

export default async function ScamReportsPage() {
  const data = await coreGet<unknown>('/trust/scam-reports/');
  const reports = asList<ScamReport>(data);

  return (
    <div>
      <PageHeader
        title="Scam Reports"
        subtitle="Overcharge reports from travellers, with the fair-price benchmark and severity."
      />
      <Panel title="Reports">
        {reports.length === 0 ? (
          <EmptyState>
            No reports to show. This view needs an admin token — set
            ADMIN_API_TOKEN to a staff JWT so the dashboard can read protected
            data.
          </EmptyState>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-zinc-200 text-zinc-500 dark:border-zinc-800">
                <tr>
                  <th className="py-2 pr-4">Service</th>
                  <th className="py-2 pr-4">Region</th>
                  <th className="py-2 pr-4">Quoted</th>
                  <th className="py-2 pr-4">Fair</th>
                  <th className="py-2 pr-4">Severity</th>
                  <th className="py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((r) => (
                  <tr key={r.id} className="border-b border-zinc-100 dark:border-zinc-900">
                    <td className="py-2 pr-4 font-medium">{r.service_type}</td>
                    <td className="py-2 pr-4">{r.region}</td>
                    <td className="py-2 pr-4">Rs. {r.quoted_price_npr}</td>
                    <td className="py-2 pr-4">
                      {r.benchmark_price_npr ? `Rs. ${r.benchmark_price_npr}` : '—'}
                    </td>
                    <td className="py-2 pr-4">
                      <span className={`rounded-full px-2 py-0.5 text-xs ${severityColor(r.scam_severity)}`}>
                        {r.scam_severity || '—'}
                      </span>
                    </td>
                    <td className="py-2 text-zinc-500">{r.status}</td>
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
