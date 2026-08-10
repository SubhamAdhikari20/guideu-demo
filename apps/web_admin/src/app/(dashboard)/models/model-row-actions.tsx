'use client';

import { Copy, Eye, MoreHorizontal } from 'lucide-react';
import { toast } from 'sonner';
import { useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';

export interface ModelCard {
  name: string;
  version: string;
  metrics: Record<string, number>;
  params: Record<string, unknown>;
  trained_at: string | null;
  n_train: number | null;
  notes: string;
}

export function ModelRowActions({ model }: { model: ModelCard }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <Button variant="ghost" size="icon-sm" aria-label={`Actions for ${model.name}`}>
              <MoreHorizontal className="size-4" />
            </Button>
          }
        />
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>{model.name}</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setOpen(true)}>
            <Eye className="size-4" /> View model card
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => {
              navigator.clipboard.writeText(model.version);
              toast.success('Version copied', { description: model.version });
            }}
          >
            <Copy className="size-4" /> Copy version
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle className="font-mono">{model.name}</DialogTitle>
            <DialogDescription>
              Trained on {model.n_train?.toLocaleString() ?? '—'} rows
              {model.trained_at ? ` · ${new Date(model.trained_at).toLocaleString()}` : ''}
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="max-h-[55vh] pr-4">
            <p className="text-sm leading-relaxed">{model.notes}</p>

            <Separator className="my-4" />
            <p className="mb-2 text-sm font-medium">Metrics</p>
            <div className="grid gap-2 sm:grid-cols-2">
              {Object.entries(model.metrics ?? {}).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between rounded-md border px-3 py-2">
                  <span className="text-muted-foreground font-mono text-xs">{key}</span>
                  <span className="text-sm font-semibold tabular-nums">{value}</span>
                </div>
              ))}
            </div>

            <Separator className="my-4" />
            <p className="mb-2 text-sm font-medium">Parameters</p>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(model.params ?? {}).map(([key, value]) => (
                <Badge key={key} variant="outline" className="font-mono text-[11px]">
                  {key}: {Array.isArray(value) ? `${value.length} items` : String(value).slice(0, 40)}
                </Badge>
              ))}
            </div>
          </ScrollArea>

          <DialogFooter>
            <DialogClose render={<Button variant="outline">Close</Button>} />
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
