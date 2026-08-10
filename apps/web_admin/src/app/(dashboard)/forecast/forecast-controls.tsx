'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useTransition } from 'react';

import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

/**
 * Year and region pickers.
 *
 * They write to the query string rather than holding state, so the page itself
 * stays a server component and the chosen forecast is a shareable URL.
 */
export function ForecastControls({
  year,
  region,
  regions,
  lastObservedYear,
}: {
  year: number;
  region: string;
  regions: string[];
  lastObservedYear: number | null;
}) {
  const router = useRouter();
  const params = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const update = (key: string, value: string) => {
    const next = new URLSearchParams(params.toString());
    if (!value || value === 'all') {
      next.delete(key);
    } else {
      next.set(key, value);
    }
    startTransition(() => router.push(`/forecast?${next.toString()}`));
  };

  // Offer the observed years plus one projection year. Anything further is
  // still reachable by URL, but the page warns loudly about it rather than
  // presenting it as a normal choice.
  const base = lastObservedYear ?? year;
  const offered = [base - 2, base - 1, base, base + 1];
  const years = Array.from(new Set([...offered, year])).sort((a, b) => a - b);

  return (
    <div className="flex flex-wrap items-end gap-4" data-pending={isPending ? '' : undefined}>
      <div className="grid gap-1.5">
        <Label htmlFor="forecast-year">Year</Label>
        <Select value={String(year)} onValueChange={(value) => update('year', String(value))}>
          <SelectTrigger id="forecast-year" className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {years.map((option) => (
              <SelectItem key={option} value={String(option)}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-1.5">
        <Label htmlFor="forecast-region">Region</Label>
        <Select value={region || 'all'} onValueChange={(value) => update('region', String(value))}>
          <SelectTrigger id="forecast-region" className="w-60">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All of Nepal</SelectItem>
            {regions.map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
