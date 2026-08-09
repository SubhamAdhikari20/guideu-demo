import dotenv from 'dotenv';
import path from 'path';

// Load the repo-root .env (shared across services), then any service-local .env.
dotenv.config({ path: path.resolve(__dirname, '../../../.env') });
dotenv.config();

export const config = {
  port: parseInt(process.env.REALTIME_PORT ?? '8002', 10),
  redisUrl: process.env.REDIS_URL ?? 'redis://localhost:6379/0',
  // core-engine REST base, used to persist chat history as it is delivered.
  coreEngineUrl: process.env.CORE_ENGINE_URL ?? 'http://localhost:8000',
  // Must equal Django's SECRET_KEY so SimpleJWT access tokens verify (HS256).
  jwtSecret: process.env.REALTIME_JWT_SECRET ?? process.env.DJANGO_SECRET_KEY ?? 'insecure-dev-key-change-in-prod',
  corsOrigins: (process.env.REALTIME_CORS_ORIGIN ?? 'http://localhost:3000')
    .split(',')
    .map((o) => o.trim())
    .filter(Boolean),
};

export type AppConfig = typeof config;
