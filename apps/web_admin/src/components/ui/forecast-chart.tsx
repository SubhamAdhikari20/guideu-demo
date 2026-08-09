/**
 * Monthly arrivals forecast — an area band with a line through it.
 *
 * The band is the point of the chart, not decoration. The forecaster was fitted
 * on three years of post-COVID recovery and reports ~17% typical error, so a
 * bare line would imply precision the model does not have. One series, so no
 * legend box is needed; the caption names it. A table view sits under the chart
 * so the numbers are readable without relying on the plot.
 */

export interface ForecastPoint {
  year: number;
  month: number;
  predicted_arrivals: number;
  lower_estimate: number;
  upper_estimate: number;
}

const MONTH_LABELS = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'];
const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

const W = 720;
const H = 260;
const PAD = { top: 16, right: 16, bottom: 28, left: 56 };

function niceCeil(value: number): number {
  const magnitude = 10 ** Math.floor(Math.log10(value));
  return Math.ceil(value / magnitude) * magnitude;
}

function compact(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${Math.round(value / 1_000)}k`;
  return String(value);
}

export function ForecastChart({ points }: { points: ForecastPoint[] }) {
  if (points.length === 0) return null;

  const max = niceCeil(Math.max(...points.map((p) => p.upper_estimate)));
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;

  const x = (i: number) => PAD.left + (points.length === 1 ? plotW / 2 : (i / (points.length - 1)) * plotW);
  const y = (v: number) => PAD.top + plotH - (v / max) * plotH;

  const line = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i)},${y(p.predicted_arrivals)}`).join(' ');
  const band = [
    ...points.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i)},${y(p.upper_estimate)}`),
    ...points.slice().reverse().map((p, i) => `L${x(points.length - 1 - i)},${y(p.lower_estimate)}`),
    'Z',
  ].join(' ');

  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => Math.round(max * f));
  const peak = points.reduce((a, b) => (b.predicted_arrivals > a.predicted_arrivals ? b : a));

  return (
    <div className="forecast-chart">
      <style>{`
        .forecast-chart {
          --series-1: #00949B;
          --grid: #e1e0d9;
          --axis: #c3c2b7;
          --ink-muted: #898781;
          --ink-secondary: #52514e;
          --surface: #ffffff;
        }
        @media (prefers-color-scheme: dark) {
          :root:where(:not([data-theme="light"])) .forecast-chart {
            --series-1: #12A0A8;
            --grid: #2c2c2a;
            --axis: #383835;
            --ink-muted: #898781;
            --ink-secondary: #c3c2b7;
            --surface: #09090b;
          }
        }
        :root[data-theme="dark"] .forecast-chart {
          --series-1: #12A0A8;
          --grid: #2c2c2a;
          --axis: #383835;
          --ink-muted: #898781;
          --ink-secondary: #c3c2b7;
          --surface: #09090b;
        }
      `}</style>

      <div className="overflow-x-auto">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full min-w-[560px]"
          role="img"
          aria-label={`Forecast monthly tourist arrivals, peaking in ${MONTH_NAMES[peak.month - 1]}`}
        >
          {ticks.map((t) => (
            <g key={t}>
              <line
                x1={PAD.left} x2={W - PAD.right} y1={y(t)} y2={y(t)}
                stroke="var(--grid)" strokeWidth={1}
              />
              <text
                x={PAD.left - 8} y={y(t) + 4} textAnchor="end"
                fill="var(--ink-muted)" fontSize={11}
                style={{ fontVariantNumeric: 'tabular-nums' }}
              >
                {compact(t)}
              </text>
            </g>
          ))}

          {/* Uncertainty band — the honest part of the forecast. */}
          <path d={band} fill="var(--series-1)" fillOpacity={0.16} />
          <path d={line} fill="none" stroke="var(--series-1)" strokeWidth={2}
                strokeLinejoin="round" strokeLinecap="round" />

          {points.map((p, i) => (
            <circle
              key={p.month} cx={x(i)} cy={y(p.predicted_arrivals)} r={4}
              fill="var(--series-1)" stroke="var(--surface)" strokeWidth={2}
            >
              <title>
                {`${MONTH_NAMES[p.month - 1]} ${p.year}: ${p.predicted_arrivals.toLocaleString()} `
                  + `(${p.lower_estimate.toLocaleString()}–${p.upper_estimate.toLocaleString()})`}
              </title>
            </circle>
          ))}

          {/* Only the peak is labelled — a number on every point is noise. */}
          <text
            x={x(points.indexOf(peak))} y={y(peak.predicted_arrivals) - 12}
            textAnchor="middle" fill="var(--ink-secondary)" fontSize={11} fontWeight={600}
          >
            {compact(peak.predicted_arrivals)}
          </text>

          <line x1={PAD.left} x2={W - PAD.right} y1={y(0)} y2={y(0)} stroke="var(--axis)" strokeWidth={1} />
          {points.map((p, i) => (
            <text
              key={p.month} x={x(i)} y={H - 8} textAnchor="middle"
              fill="var(--ink-muted)" fontSize={11}
            >
              {MONTH_LABELS[p.month - 1]}
            </text>
          ))}
        </svg>
      </div>

      <details className="mt-4">
        <summary className="cursor-pointer text-sm text-zinc-500">View as table</summary>
        <table className="mt-2 w-full text-left text-sm">
          <thead className="border-b border-zinc-200 text-zinc-500 dark:border-zinc-800">
            <tr>
              <th className="py-1.5 pr-4">Month</th>
              <th className="py-1.5 pr-4">Forecast</th>
              <th className="py-1.5">Likely range</th>
            </tr>
          </thead>
          <tbody style={{ fontVariantNumeric: 'tabular-nums' }}>
            {points.map((p) => (
              <tr key={p.month} className="border-b border-zinc-100 dark:border-zinc-900">
                <td className="py-1.5 pr-4">{MONTH_NAMES[p.month - 1]}</td>
                <td className="py-1.5 pr-4 font-medium">{p.predicted_arrivals.toLocaleString()}</td>
                <td className="py-1.5 text-zinc-500">
                  {p.lower_estimate.toLocaleString()} – {p.upper_estimate.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
