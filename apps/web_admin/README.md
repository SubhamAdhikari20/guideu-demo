# GuideU Web Admin (`apps/web_admin`)

Next.js 16 App Router dashboard for GuideU administrators and moderators, built
on **shadcn/ui** (Base UI primitives + Tailwind v4).

## Routes

- `/dashboard` — catalog counts, model summary cards, trust tab
- `/models` — analytics-engine model registry with per-model detail
- `/forecast` — projected monthly arrivals with the model's error band
- `/festivals` — cultural-event calendar by month
- `/scam-reports` — report queue with moderation actions

Server Components perform every protected read, so `ANALYTICS_API_KEY` and
`ADMIN_API_TOKEN` never reach the browser bundle. Backend outages render as
empty states rather than crashing a page, and the header shows which services
are actually reachable — the app degrades *silently* when the ML service is
down, so an explicit indicator is the only way to tell the two apart.

## UI components

Built with shadcn/ui. Components live in `src/components/ui/` and are owned by
this repo (shadcn copies source in rather than shipping a dependency), so they
can be edited directly.

| Component | Where it does real work |
|---|---|
| `sidebar` | Collapsible app navigation with icon-only mode and tooltips |
| `breadcrumb` | Route trail in the sticky header |
| `card` | Stat tiles, page sections, model summaries |
| `table` | Model registry, scam-report queue, festival calendar, forecast table |
| `badge` | Severity, status, headline metrics, service counts |
| `dropdown-menu` | Row actions on models and reports; theme picker |
| `alert-dialog` | Confirming a verify/dismiss before it changes a provider's standing |
| `dialog` | Model card details, full scam-report detail |
| `popover` | Metric glossaries, service health, forecast caveat |
| `tooltip` | Benchmark values, model caveats, collapsed sidebar labels |
| `tabs` | Dashboard sections, chart/table view switch |
| `select` + `label` | Forecast year and region pickers |
| `sonner` | Toasts confirming or reporting moderation failures |
| `separator`, `scroll-area`, `skeleton` | Layout and loading detail |

Add more with `npx shadcn@latest add <component>`.

### Theme

`src/app/globals.css` carries the shadcn token set with GuideU's brand applied:
`--primary` is the wordmark teal (`#138086`), and `--chart-1..4` are the
validated GuideU categorical palette (teal, gold, violet, red) — checked for
lightness band, chroma floor, colour-vision-deficiency separation,
normal-vision separation and contrast on both surfaces. Dark mode is a
class-based `next-themes` switch with its own re-stepped values, not a flip.

## Local development

```bash
npm ci
npm run dev
```

The app listens on `http://localhost:3000`. Configure:

- `CORE_API_BASE_URL` (default `http://localhost:8000/api/v1`)
- `ANALYTICS_ENGINE_URL` (default `http://localhost:8001`)
- `ANALYTICS_API_KEY` (must match the analytics-engine's key)
- `ADMIN_API_TOKEN` — a staff JWT. Without it the dashboard runs read-only and
  says so; moderation actions are disabled rather than failing at the click.

To get a staff token locally:

```bash
cd ../../services/core-engine
python manage.py createsuperuser
curl -s -X POST http://localhost:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"..."}'
```

## Moderation

`/scam-reports` calls the core-engine's existing `verify` and `dismiss` actions
through Server Actions (`src/lib/actions/moderation.ts`), so the staff token
stays server-side. Each action is confirmed with an `alert-dialog` first —
verifying a report changes a provider's standing — and the result is reported
with a toast. A failure is surfaced loudly, because a silent one would leave a
moderator believing a report had been actioned when it had not.
