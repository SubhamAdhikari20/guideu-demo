import { Activity } from 'lucide-react';

import { ServiceStatusPopover, type ServiceState } from './service-status-popover';
import { adminTokenStatus, coreGet, mlGet } from '@/lib/api/server';

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
  const [health, catalog, tokenState] = await Promise.all([
    mlGet<Health>('/health'),
    coreGet<{ count?: number }>('/catalog/regions/?page_size=1'),
    adminTokenStatus(),
  ]);

  const TOKEN_DETAIL: Record<typeof tokenState, string> = {
    active: 'Authenticated administrator session; moderation actions enabled',
    expired: 'Administrator session expired; sign in again',
    missing: 'No administrator session',
  };

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
      name: 'admin session',
      detail: TOKEN_DETAIL[tokenState],
      online: tokenState === 'active',
    },
  ];

  return <ServiceStatusPopover services={services} icon={<Activity className="size-4" />} />;
}
