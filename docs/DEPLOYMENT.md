# GuideU — Deployment

GuideU ships as a set of Docker images orchestrated by Docker Compose. Local
development uses `docker-compose.yml`; production uses `docker-compose.prod.yml`.

## Prerequisites
- Docker + Docker Compose v2 on the host.
- A filled-in repo-root `.env` (copy `.env.example`). For production set:
  - a real `DJANGO_SECRET_KEY` (32+ chars)
  - strong `POSTGRES_PASSWORD`, `MONGO_INITDB_ROOT_PASSWORD`
  - `DJANGO_ALLOWED_HOSTS` (your domain) and `CORS_ALLOWED_ORIGINS`
  - a non-default `ANALYTICS_API_KEY`

## What's different in production
- `DJANGO_SETTINGS_MODULE=config.settings.prod` — DEBUG off, SSL redirect, HSTS,
  secure cookies, JWT refresh-token blacklisting (see `docs/architecture/SECURITY.md`).
- core-engine runs under **gunicorn** (4 workers) and runs `migrate` +
  `collectstatic` on boot.
- Datastores are **not** published to the host — only Nginx is public (80/443).
- Every service has `restart: always`.
- Static and media are shared with Nginx through named volumes.
- The Next.js admin is built as a standalone Node image and is available only
  through the Nginx gateway.

## Deploy
```bash
cp .env.example .env        # then edit it with real values
./scripts/deploy.sh         # builds images and starts the stack
```
Or directly:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## After deploy
```bash
# create an admin user
docker compose -f docker-compose.prod.yml exec core-engine python manage.py createsuperuser

# seed the catalog from the dataset (routes, guides, festivals, benchmarks)
docker compose -f docker-compose.prod.yml exec core-engine python manage.py seed_from_dataset
```

## TLS
Terminate TLS at Nginx (add a 443 server block with your certificate, e.g. via
Let's Encrypt / certbot) or behind a managed load balancer. The app already sets
`SECURE_PROXY_SSL_HEADER`, so it trusts `X-Forwarded-Proto` from the proxy.

## Frontends
- Web admin (Next.js): included in both Compose files. Server-side API URLs are
  overridden to use the internal Compose service names, while Nginx serves the
  dashboard at `/`.
- Mobile (Flutter): build with `--dart-define GUIDEU_API_BASE_URL=...` and
  `--dart-define GUIDEU_REALTIME_URL=...` pointing at the gateway, then ship the
  APK / IPA.

## Future work
- Kubernetes manifests / Helm chart for horizontal scaling.
- Managed Postgres + Redis instead of in-cluster containers.
- Automated backups for Postgres and Mongo volumes.
