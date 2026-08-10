'use client';

import { Monitor, Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';

import { useHydrated } from '@/hooks/use-hydrated';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export function ThemeToggle() {
  const { setTheme, theme } = useTheme();
  // The server cannot know the resolved theme, so show the light icon until
  // hydration rather than flashing the wrong one.
  const mounted = useHydrated();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger render={
        <Button variant="ghost" size="icon" aria-label="Change theme">
          {mounted && theme === 'dark' ? <Moon className="size-4" /> : <Sun className="size-4" />}
        </Button>
      } />
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setTheme('light')}>
          <Sun className="size-4" /> Light
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('dark')}>
          <Moon className="size-4" /> Dark
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('system')}>
          <Monitor className="size-4" /> System
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
