import { Activity } from 'lucide-react';

import { ServiceStatusPopover, type ServiceState } from './service-status-popover';
import { coreGet, hasAdminToken, mlGet } from '@/lib/api/server';

interface Health {
  status?: string;
  models?: Record<string, string>;
}

/**
 * Live reachability of the two backends, shown in the header.
 *
 * Worth surfacing because both the app and this dashboard degrade *silently*
 * when the analytics-engine is unreachable — the recommendation feed quietly
 * serves its non-personalised fallback. Without an indicator, "the ML is down"
 * and "the ML is working" look identical from the outside.
 */
export async function ServiceStatus() {
  const [health, catalog] = await Promise.all([
    mlGet<Health>('/health'),
    coreGet<{ count?: number }>('/catalog/regions/?page_size=1'),
  ]);

  const services: ServiceState[] = [
    {
      name: 'core-engine',
      detail: catalog ? `Catalog reachable · ${catalog.count ?? 0} regions` : 'Not reachable on the configured URL',
      online: Boolean(catalog),
    },
    {
      name: 'analytics-engine',
      detail: health
        ? `${Object.keys(health.models ?? {}).length} models registered`
        : 'Not reachable — feeds will fall back to a non-personalised ordering',
      online: Boolean(health),
    },
    {
      name: 'staff token',
      detail: hasAdminToken
        ? 'Configured — moderation actions enabled'
        : 'Not set — moderation actions are read-only (set ADMIN_API_TOKEN)',
      online: hasAdminToken,
    },
  ];

  return <ServiceStatusPopover services={services} icon={<Activity className="size-4" />} />;
}
