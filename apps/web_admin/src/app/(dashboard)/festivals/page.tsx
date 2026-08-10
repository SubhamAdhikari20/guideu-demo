import { PageHeader } from '@/components/layout/page-header';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { coreGet } from '@/lib/api/server';

interface Festival {
  festival_name: string;
  event_type: string;
  significance: string;
  duration_days: number;
  regions: string[];
}

interface FestivalMonth {
  month: number;
  month_name: string;
  festivals: Festival[];
}

export const dynamic = 'force-dynamic';

const SIGNIFICANCE_VARIANT: Record<string, 'default' | 'secondary' | 'outline'> = {
  High: 'default',
  Medium: 'secondary',
  Low: 'outline',
};

export default async function FestivalsPage() {
  const data = await coreGet<{ months: FestivalMonth[] }>('/catalog/events/upcoming/?months=12');
  const months = (data?.months ?? []).filter((m) => m.festivals.length > 0);
  const total = months.reduce((sum, m) => sum + m.festivals.length, 0);

  return (
    <div>
      <PageHeader
        title="Festivals &amp; events"
        subtitle="The information-hub calendar shown to travellers, grouped by month."
        actions={
          <Badge variant="secondary" className="tabular-nums">
            {total} over 12 months
          </Badge>
        }
      />

      {months.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground rounded-lg border border-dashed p-8 text-center text-sm">
              No festivals found. Seed the catalog with{' '}
              <code className="bg-muted rounded px-1 py-0.5 text-xs">
                manage.py seed_from_dataset
              </code>{' '}
              to populate the calendar.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {months.map((month) => (
            <Card key={month.month}>
              <CardHeader>
                <CardTitle>{month.month_name}</CardTitle>
                <CardDescription>
                  {month.festivals.length} festival{month.festivals.length === 1 ? '' : 's'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Festival</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="text-right">Days</TableHead>
                      <TableHead>Significance</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {month.festivals.map((festival) => (
                      <TableRow key={`${month.month}-${festival.festival_name}`}>
                        <TableCell>
                          <div className="font-medium">{festival.festival_name}</div>
                          <div className="text-muted-foreground text-xs">
                            {festival.regions.length > 0
                              ? festival.regions.join(', ')
                              : 'Across Nepal'}
                          </div>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {festival.event_type}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {festival.duration_days}
                        </TableCell>
                        <TableCell>
                          <Badge variant={SIGNIFICANCE_VARIANT[festival.significance] ?? 'outline'}>
                            {festival.significance}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
