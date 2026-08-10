'use client';

import {
  BrainCircuit,
  CalendarDays,
  LayoutDashboard,
  MountainSnow,
  ShieldAlert,
  TrendingUp,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar';

const SECTIONS = [
  {
    label: 'Platform',
    items: [
      { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
      { href: '/festivals', label: 'Festivals', icon: CalendarDays },
    ],
  },
  {
    label: 'Machine learning',
    items: [
      { href: '/models', label: 'Model registry', icon: BrainCircuit },
      { href: '/forecast', label: 'Demand forecast', icon: TrendingUp },
    ],
  },
  {
    label: 'Trust & safety',
    items: [{ href: '/scam-reports', label: 'Scam reports', icon: ShieldAlert }],
  },
] as const;

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              size="lg"
              tooltip="GuideU Admin"
              render={<Link href="/dashboard" />}
            >
              <div className="bg-primary text-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                <MountainSnow className="size-4" />
              </div>
              <div className="grid flex-1 text-left leading-tight">
                <span className="truncate font-semibold">GuideU</span>
                <span className="text-muted-foreground truncate text-xs">Admin console</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        {SECTIONS.map((section) => (
          <SidebarGroup key={section.label}>
            <SidebarGroupLabel>{section.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {section.items.map((item) => {
                  const active =
                    pathname === item.href || pathname.startsWith(`${item.href}/`);
                  return (
                    <SidebarMenuItem key={item.href}>
                      <SidebarMenuButton
                        isActive={active}
                        tooltip={item.label}
                        render={<Link href={item.href} />}
                      >
                        <item.icon />
                        <span>{item.label}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter>
        <div className="text-muted-foreground group-data-[collapsible=icon]:hidden px-2 pb-1 text-xs">
          Reads the catalog from the core-engine and the model registry from the
          analytics-engine.
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
