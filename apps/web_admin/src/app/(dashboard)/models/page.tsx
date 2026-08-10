import { AlertTriangle } from 'lucide-react';

import { PageHeader } from '@/components/layout/page-header';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { mlGet } from '@/lib/api/server';

import { ModelRowActions, type ModelCard } from './model-row-actions';

export const dynamic = 'force-dynamic';

/** Which metric leads each row, and what it should be read against. */
const HEADLINE: Record<string, { key: string; label: string; explain: string }> = {
  scam_classifier: {
    key: 'f1',
    label: 'F1',
    explain: 'Harmonic mean of precision and recall. The majority-class baseline scores 0.000.',
  },
  route_recommender: {
    key: 'model_only_lift_over_popularity',
    label: 'Lift',
    explain:
      'Hit-rate@10 divided by a popularity-only baseline. Above 1.0 means personalisation is helping.',
  },
  guide_ranker: {
    key: 'rmse',
    label: 'RMSE',
    explain: 'Error in predicted 1-5 rating. Lower is better; predicting the mean scores 0.688.',
  },
  arrivals_forecaster: {
    key: 'mape',
    label: 'MAPE',
    explain: 'Mean absolute percentage error. Lower is better; a seasonal naive forecast scores 38.6%.',
  },
  tourist_segments: {
    key: 'silhouette',
    label: 'Silhouette',
    explain:
      'Cluster separation, 0-1. This sits near 0.13 for every k, which means there is no natural cluster structure — reported rather than hidden.',
  },
};

/** Models whose headline number needs a caveat rather than a clean tick. */
const CAVEATS: Record<string, string> = {
  tourist_segments:
    'Weak clusters by design: silhouette stays ~0.13 at every k, so these segments are an operational cold-start device, not discovered personas.',
  arrivals_forecaster:
    'Wins on the 2024 test year but loses to a seasonal naive forecast on the 2023 validation year — three years of post-COVID data is not enough for stable model selection.',
};

export default async function ModelsPage() {
  const models = await mlGet<ModelCard[]>('/api/v1/models');

  return (
    <div>
      <PageHeader
        title="Model registry"
        subtitle="Every trained model, its headline metric and the baseline it was measured against."
      />

      <Card>
        <CardHeader>
          <CardTitle>Registered models</CardTitle>
          <CardDescription>
            Read live from the analytics-engine. Regenerate with{' '}
            <code className="bg-muted rounded px-1 py-0.5 text-xs">python -m training.run_all</code>.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!models || models.length === 0 ? (
            <p className="text-muted-foreground rounded-lg border border-dashed p-8 text-center text-sm">
              No models found. Start the analytics-engine and train the models, or check
              ANALYTICS_ENGINE_URL / ANALYTICS_API_KEY.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Model</TableHead>
                    <TableHead>Headline metric</TableHead>
                    <TableHead className="text-right">Training rows</TableHead>
                    <TableHead>Version</TableHead>
                    <TableHead className="w-10" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {models.map((model) => {
                    const headline = HEADLINE[model.name];
                    const value = headline ? model.metrics?.[headline.key] : undefined;
                    const caveat = CAVEATS[model.name];
                    return (
                      <TableRow key={model.version}>
                        <TableCell className="font-mono font-medium">
                          <div className="flex items-center gap-2">
                            {model.name}
                            {caveat && (
                              <Tooltip>
                                <TooltipTrigger
                                  render={
                                    <AlertTriangle className="size-3.5 text-amber-600 dark:text-amber-500" />
                                  }
                                />
                                <TooltipContent className="max-w-xs">{caveat}</TooltipContent>
                              </Tooltip>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {headline ? (
                            <Popover>
                              <PopoverTrigger
                                render={
                                  <Badge variant="secondary" className="cursor-help tabular-nums">
                                    {headline.label} {value ?? '—'}
                                  </Badge>
                                }
                              />
                              <PopoverContent className="w-80 text-sm">
                                <p className="font-medium">{headline.label}</p>
                                <p className="text-muted-foreground mt-1 text-xs leading-relaxed">
                                  {headline.explain}
                                </p>
                              </PopoverContent>
                            </Popover>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {model.n_train?.toLocaleString() ?? '—'}
                        </TableCell>
                        <TableCell className="text-muted-foreground font-mono text-xs">
                          {model.version}
                        </TableCell>
                        <TableCell>
                          <ModelRowActions model={model} />
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
