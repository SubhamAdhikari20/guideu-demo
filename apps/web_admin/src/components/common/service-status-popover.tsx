'use client';

import type { ReactNode } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

export interface ServiceState {
  name: string;
  detail: string;
  online: boolean;
}

export function ServiceStatusPopover({
  services,
  icon,
}: {
  services: ServiceState[];
  icon: ReactNode;
}) {
  const down = services.filter((s) => !s.online).length;

  return (
    <Popover>
      <PopoverTrigger
        render={
          <Button variant="ghost" size="sm" className="gap-2" aria-label="Service status">
            {icon}
            <span className="hidden sm:inline">Services</span>
            <Badge variant={down === 0 ? 'secondary' : 'destructive'} className="tabular-nums">
              {services.length - down}/{services.length}
            </Badge>
          </Button>
        }
      />
      <PopoverContent align="end" className="w-80">
        <div className="space-y-1">
          <p className="text-sm font-medium">Backend services</p>
          <p className="text-muted-foreground text-xs">
            Checked when this page was rendered.
          </p>
        </div>
        <Separator className="my-3" />
        <ul className="space-y-3">
          {services.map((service) => (
            <li key={service.name} className="flex gap-3">
              <span
                aria-hidden
                className={cn(
                  'mt-1.5 size-2 shrink-0 rounded-full',
                  service.online ? 'bg-emerald-500' : 'bg-destructive',
                )}
              />
              <div className="min-w-0">
                <p className="font-mono text-xs font-medium">{service.name}</p>
                <p className="text-muted-foreground text-xs">{service.detail}</p>
              </div>
            </li>
          ))}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
