'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const links = [
  { href: '/dashboard', label: 'Overview' },
  { href: '/models', label: 'ML Models' },
  { href: '/festivals', label: 'Festivals' },
  { href: '/scam-reports', label: 'Scam Reports' },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 shrink-0 border-r border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="mb-6 px-2">
        <span className="text-xl font-bold text-[#138086]">GuideU</span>
        <span className="ml-1 text-sm text-zinc-500">Admin</span>
      </div>
      <nav className="flex flex-col gap-1">
        {links.map((link) => {
          const active =
            pathname === link.href || pathname.startsWith(`${link.href}/`);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={
                'rounded-lg px-3 py-2 text-sm font-medium transition-colors ' +
                (active
                  ? 'bg-[#138086] text-white'
                  : 'text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-900')
              }
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
