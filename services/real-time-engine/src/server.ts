import cors from 'cors';
import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';

import { config } from './config';
import { logger } from './logger';
import { startRedisBridge } from './redisBridge';
import { attachSocketHandlers } from './socket';

async function main(): Promise<void> {
  const app = express();
  app.use(cors({ origin: config.corsOrigins }));
  app.use(express.json());

  app.get('/health', (_req, res) => {
    res.json({ status: 'healthy', service: 'guideu-real-time-engine' });
  });

  const httpServer = createServer(app);
  const io = new Server(httpServer, {
    cors: { origin: config.corsOrigins, methods: ['GET', 'POST'] },
  });

  attachSocketHandlers(io);

  // Bind the port first: chat only needs Socket.IO, so the service must come up
  // whether or not the optional Redis event bridge is reachable.
  httpServer.listen(config.port, () => {
    logger.info('real-time-engine listening', { port: config.port });
  });

  const stopBridge = await startRedisBridge(io);

  const shutdown = async (signal: string): Promise<void> => {
    logger.info('shutting down', { signal });
    await stopBridge().catch(() => undefined);
    io.close();
    httpServer.close(() => process.exit(0));
    // Force-exit if connections linger.
    setTimeout(() => process.exit(0), 5000).unref();
  };

  process.on('SIGINT', () => void shutdown('SIGINT'));
  process.on('SIGTERM', () => void shutdown('SIGTERM'));
}

main().catch((err) => {
  logger.error('fatal startup error', { err: String(err) });
  process.exit(1);
});
