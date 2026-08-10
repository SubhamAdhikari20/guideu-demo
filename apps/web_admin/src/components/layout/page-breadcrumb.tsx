'use client';

import { usePathname } from 'next/navigation';
import { Fragment } from 'react';

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';

const TITLES: Record<string, string> = {
  dashboard: 'Overview',
  models: 'Model registry',
  forecast: 'Demand forecast',
  festivals: 'Festivals',
  'scam-reports': 'Scam reports',
};

export function PageBreadcrumb() {
  const segments = usePathname().split('/').filter(Boolean);

  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem className="hidden md:block">
          <BreadcrumbLink href="/dashboard">GuideU Admin</BreadcrumbLink>
        </BreadcrumbItem>
        {segments.map((segment, index) => {
          const isLast = index === segments.length - 1;
          const label = TITLES[segment] ?? segment;
          return (
            <Fragment key={segment}>
              <BreadcrumbSeparator className="hidden md:block" />
              <BreadcrumbItem>
                {isLast ? (
                  <BreadcrumbPage>{label}</BreadcrumbPage>
                ) : (
                  <BreadcrumbLink href={`/${segments.slice(0, index + 1).join('/')}`}>
                    {label}
                  </BreadcrumbLink>
                )}
              </BreadcrumbItem>
            </Fragment>
          );
        })}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
