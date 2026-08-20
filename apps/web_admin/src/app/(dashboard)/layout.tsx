import { AppSidebar } from '@/components/layout/app-sidebar';
import { PageBreadcrumb } from '@/components/layout/page-breadcrumb';
import { ThemeToggle } from '@/components/layout/theme-toggle';
import { ServiceStatus } from '@/components/common/service-status';
import { Separator } from '@/components/ui/separator';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { requireAdmin } from '@/lib/auth';
import { logoutAction } from '@/app/login/actions';
import { LogOut } from 'lucide-react';

export default async function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const admin = await requireAdmin();
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="bg-background/95 supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b backdrop-blur">
          <div className="flex flex-1 items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
            <PageBreadcrumb />
          </div>
          <div className="flex items-center gap-2 px-4">
            <span className="text-muted-foreground hidden text-xs md:inline">{admin.first_name || admin.email}</span>
            <ServiceStatus />
            <ThemeToggle />
            <form action={logoutAction}><Button type="submit" size="icon" variant="ghost" aria-label="Sign out"><LogOut className="size-4" /></Button></form>
          </div>
        </header>
        <main className="flex flex-1 flex-col gap-4 p-4 md:p-6">{children}</main>
      </SidebarInset>
    </SidebarProvider>
  );
}
