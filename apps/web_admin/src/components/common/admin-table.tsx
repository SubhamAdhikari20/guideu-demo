import type { ReactNode } from 'react';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export function AdminTable({ columns, rows, empty = 'No records found.' }: {
  columns: { key: string; label: string }[];
  rows: ({ id: string | number } & Record<string, ReactNode>)[];
  empty?: string;
}) {
  return (
    <div className="overflow-hidden rounded-lg border">
      <Table>
        <TableHeader><TableRow>{columns.map((column) => <TableHead key={column.key}>{column.label}</TableHead>)}</TableRow></TableHeader>
        <TableBody>
          {rows.map((row) => <TableRow key={row.id}>{columns.map((column) => <TableCell key={column.key}>{row[column.key]}</TableCell>)}</TableRow>)}
          {!rows.length && <TableRow><TableCell colSpan={columns.length} className="text-muted-foreground h-24 text-center">{empty}</TableCell></TableRow>}
        </TableBody>
      </Table>
    </div>
  );
}
