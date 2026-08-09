import { Sidebar } from '@/components/layout/sidebar';

export default function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 bg-zinc-50 p-8 dark:bg-zinc-900">{children}</main>
    </div>
  );
}
