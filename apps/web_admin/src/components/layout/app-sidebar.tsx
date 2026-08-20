'use client';

import {
  BrainCircuit,
  CalendarDays,
  LayoutDashboard,
  MountainSnow,
  ShieldAlert,
  TrendingUp,
  UserCheck,
  ReceiptText,
  Star,
  Siren,
  PackageSearch,
  Users,
} from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import {
  Sidebar,
  SidebarContent,
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
      { href: '/users', label: 'Users', icon: Users },
      { href: '/guides', label: 'Guide verification', icon: UserCheck },
      { href: '/bookings', label: 'Bookings', icon: CalendarDays },
      { href: '/payments', label: 'Payments', icon: ReceiptText },
      { href: '/inventory', label: 'Travel inventory', icon: PackageSearch },
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
    items: [
      { href: '/scam-reports', label: 'Scam reports', icon: ShieldAlert },
      { href: '/reviews', label: 'Reviews', icon: Star },
      { href: '/safety', label: 'SOS response', icon: Siren },
    ],
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
              {/* The brand asset is a wordmark, so it only works at full width.
                  Collapsed to icon width it would be illegible — the compact
                  mark below stands in for it there. */}
              <div className="bg-primary text-primary-foreground hidden aspect-square size-8 items-center justify-center rounded-lg group-data-[collapsible=icon]:flex">
                <MountainSnow className="size-4" />
              </div>
              <div className="grid flex-1 gap-0.5 text-left leading-tight group-data-[collapsible=icon]:hidden">
                <Image
                  src="/guideu-logo.png"
                  alt="GuideU"
                  width={955}
                  height={261}
                  priority
                  className="h-6 w-auto object-contain object-left"
                />
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

      {/* <SidebarFooter>
        <div className="text-muted-foreground group-data-[collapsible=icon]:hidden px-2 pb-1 text-xs">
          Reads the catalog from the core-engine and the model registry from the
          analytics-engine.
        </div>
      </SidebarFooter> */}
      <SidebarRail />
    </Sidebar>
  );
}
