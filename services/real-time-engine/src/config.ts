import dotenv from 'dotenv';
import path from 'path';

// Load the repo-root .env (shared across services), then any service-local .env.
dotenv.config({ path: path.resolve(__dirname, '../../../.env') });
dotenv.config();

/**
 * Django's own development fallback for SECRET_KEY (see the core-engine's
 * `config/settings/base.py`). SimpleJWT signs access tokens with it, so this
 * service has to fall back to exactly the same string — the two defaults used
 * to differ, which meant that with no `.env` present every socket handshake was
 * rejected as "invalid token" and live chat simply did not work.
 *
 * Both compose files set REALTIME_JWT_SECRET explicitly, so deployments are
 * unaffected; this only makes a bare local run behave.
 */
const DJANGO_INSECURE_DEV_SECRET = 'insecure-development-key-change-in-production';

export const config = {
  port: parseInt(process.env.REALTIME_PORT ?? '8002', 10),
  redisUrl: process.env.REDIS_URL ?? 'redis://localhost:6379/0',
  // core-engine REST base, used to persist chat history as it is delivered.
  coreEngineUrl: process.env.CORE_ENGINE_URL ?? 'http://localhost:8000',
  // Must equal Django's SECRET_KEY so SimpleJWT access tokens verify (HS256).
  jwtSecret:
    process.env.REALTIME_JWT_SECRET ?? process.env.DJANGO_SECRET_KEY ?? DJANGO_INSECURE_DEV_SECRET,
  corsOrigins: (process.env.REALTIME_CORS_ORIGIN ?? 'http://localhost:3000')
    .split(',')
    .map((o) => o.trim())
    .filter(Boolean),
};

export type AppConfig = typeof config;
