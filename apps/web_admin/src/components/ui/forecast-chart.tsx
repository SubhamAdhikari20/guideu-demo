/**
 * Monthly arrivals forecast — an area band with a line through it.
 *
 * The band is the point of the chart, not decoration. The forecaster was fitted
 * on three years of post-COVID recovery and reports ~17% typical error, so a
 * bare line would imply precision the model does not have. One series, so no
 * legend is needed; the card title names it. A table view sits under the chart
 * so the numbers are readable without relying on the plot.
 *
 * Colours come from the theme's `--chart-1` token, so light and dark are both
 * handled by the same class-based switch the rest of the dashboard uses.
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

  const x = (i: number) =>
    PAD.left + (points.length === 1 ? plotW / 2 : (i / (points.length - 1)) * plotW);
  const y = (v: number) => PAD.top + plotH - (v / max) * plotH;

  const line = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i)},${y(p.predicted_arrivals)}`)
    .join(' ');
  const band = [
    ...points.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i)},${y(p.upper_estimate)}`),
    ...points
      .slice()
      .reverse()
      .map((p, i) => `L${x(points.length - 1 - i)},${y(p.lower_estimate)}`),
    'Z',
  ].join(' ');

  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => Math.round(max * f));
  const peak = points.reduce((a, b) => (b.predicted_arrivals > a.predicted_arrivals ? b : a));

  return (
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
              x1={PAD.left}
              x2={W - PAD.right}
              y1={y(t)}
              y2={y(t)}
              className="stroke-border"
              strokeWidth={1}
            />
            <text
              x={PAD.left - 8}
              y={y(t) + 4}
              textAnchor="end"
              className="fill-muted-foreground tabular-nums"
              fontSize={11}
            >
              {compact(t)}
            </text>
          </g>
        ))}

        {/* Uncertainty band — the honest part of the forecast. */}
        <path d={band} fill="var(--chart-1)" fillOpacity={0.16} />
        <path
          d={line}
          fill="none"
          stroke="var(--chart-1)"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {points.map((p, i) => (
          <circle
            key={p.month}
            cx={x(i)}
            cy={y(p.predicted_arrivals)}
            r={4}
            fill="var(--chart-1)"
            className="stroke-card"
            strokeWidth={2}
          >
            <title>
              {`${MONTH_NAMES[p.month - 1]} ${p.year}: ${p.predicted_arrivals.toLocaleString()} ` +
                `(${p.lower_estimate.toLocaleString()}–${p.upper_estimate.toLocaleString()})`}
            </title>
          </circle>
        ))}

        {/* Only the peak is labelled — a number on every point is noise. */}
        <text
          x={x(points.indexOf(peak))}
          y={y(peak.predicted_arrivals) - 12}
          textAnchor="middle"
          className="fill-foreground"
          fontSize={11}
          fontWeight={600}
        >
          {compact(peak.predicted_arrivals)}
        </text>

        <line
          x1={PAD.left}
          x2={W - PAD.right}
          y1={y(0)}
          y2={y(0)}
          className="stroke-muted-foreground/40"
          strokeWidth={1}
        />
        {points.map((p, i) => (
          <text
            key={p.month}
            x={x(i)}
            y={H - 8}
            textAnchor="middle"
            className="fill-muted-foreground"
            fontSize={11}
          >
            {MONTH_LABELS[p.month - 1]}
          </text>
        ))}
      </svg>
    </div>
  );
}
