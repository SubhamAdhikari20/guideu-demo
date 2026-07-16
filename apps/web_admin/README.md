# GuideU Web Admin (`apps/web_admin`)

Next.js 16 App Router dashboard for GuideU administrators and moderators. The
current thesis scope is deliberately read-only: overview metrics, ML model
registry, festivals and scam reports. A dedicated login flow and moderation
write actions are documented future work.

## Routes

- `/dashboard` — overview metrics
- `/models` — analytics-engine model registry
- `/festivals` — cultural-event calendar
- `/scam-reports` — protected report listing when an admin JWT is configured

Server Components perform protected reads so `ANALYTICS_API_KEY` and
`ADMIN_API_TOKEN` are never included in the browser bundle. Backend outages are
handled as empty/error states instead of crashing a dashboard page.

## Local development

```bash
npm ci
npm run dev
```

The app listens on `http://localhost:3000`. Configure:

- `CORE_API_BASE_URL` (default `http://localhost:8000/api/v1`)
- `ANALYTICS_ENGINE_URL` (default `http://localhost:8001`)
- `ANALYTICS_API_KEY`
- `ADMIN_API_TOKEN` (optional staff JWT for protected core-engine reads)
- `NEXT_PUBLIC_API_BASE_URL` (only for future browser-side API calls)

## Production

The repository Dockerfile uses Next.js standalone output. Both root Compose
files build the image, inject internal service URLs at runtime and place the app
behind Nginx. Validate changes with:

```bash
npm run lint
npm run build
```
