# GuideU — Security Measures

This maps to the thesis ethics & data-protection chapter. GuideU handles personal
data (names, emails, locations, payments), so security is layered across the stack.

## Authentication & sessions
- JWT auth (SimpleJWT): short-lived access tokens, refresh tokens.
- Refresh-token **rotation + blacklisting** in production (`settings/prod.py`).
- Password validators: minimum length, common-password and numeric-only checks,
  and similarity-to-user-attributes (`AUTH_PASSWORD_VALIDATORS`).

## Rate limiting (anti-abuse / anti-brute-force)
DRF throttling, configured in `settings/base.py`:
- `login` — 10/min per IP on the token endpoint.
- `register` — 5/min per IP.
- `scam_check` — 30/min on the anti-scam tool.
- Global `anon` 60/min, `user` 1000/hour defaults.

## Input handling (anti-XSS / injection)
- All write APIs go through DRF serializers with typed field validation.
- Free-text fields (chat messages, itinerary titles, SOS notes) are passed
  through `src/common/sanitize.clean_text`, which strips HTML tags before storage,
  so no user can inject markup that another user's client would render.
- The ORM parametrises all queries (no raw SQL in app code) — SQL injection safe.

## Authorisation (data isolation)
- Bookings, payments, chat threads, travel workspaces and SOS alerts are all
  scoped to `request.user`; staff-only actions use `IsAdminUser`.
- Chat rooms enforce participant membership before read or write.

## Transport & browser security (production)
`settings/prod.py`: `SECURE_SSL_REDIRECT`, HSTS (1 year, subdomains, preload),
`SECURE_PROXY_SSL_HEADER`, secure session/CSRF cookies, `nosniff`, `X-Frame-Options: DENY`.
The Nginx gateway also adds `X-Frame-Options`, `X-Content-Type-Options`,
`Referrer-Policy` and `X-XSS-Protection` headers as defence in depth.

## CORS
- Production allows only explicit origins (`CORS_ALLOWED_ORIGINS`); `CORS_ALLOW_ALL_ORIGINS`
  is enabled **only** in `settings/dev.py`.

## Secrets
- No secrets in the repo (verified by audit). All keys come from environment
  variables; `.env.example` documents them with placeholder values.
- The ML service is guarded by an internal `X-API-Key`; the realtime engine
  verifies the same JWT signing key as Django.

## Known gaps / future work
- Add 2FA for admin accounts.
- Move to per-user (not per-IP) login throttling once accounts scale.
- Add automated dependency-vulnerability scanning in CI.
