import { AdminTable } from '@/components/common/admin-table';
import { PageHeader } from '@/components/layout/page-header';
import { Badge } from '@/components/ui/badge';
import { asList, coreGet } from '@/lib/api/server';

export const dynamic = 'force-dynamic';
interface PaymentRow { id: number; user: number; booking?: number; guide_request?: number; service_booking?: number; amount: string; currency: string; status: string; gateway: string; mode: string; gateway_reference?: string; verified_at?: string; created_at: string }

export default async function PaymentsPage() {
  const payments = asList<PaymentRow>(await coreGet('/payments/payments/?page_size=100'));
  return <div><PageHeader title="Payments and escrow" subtitle="Provider, verification, and booking-target audit trail. Redirects alone never count as payment." />
    <AdminTable columns={[{ key: 'idLabel', label: 'Payment' }, { key: 'target', label: 'Target' }, { key: 'amount', label: 'Amount' }, { key: 'provider', label: 'Provider' }, { key: 'status', label: 'Status' }, { key: 'created', label: 'Created' }]}
      rows={payments.map((payment) => ({
        id: payment.id,
        idLabel: <div><p className="font-mono">#{payment.id}</p><p className="text-muted-foreground max-w-40 truncate text-xs">{payment.gateway_reference || 'Not initiated'}</p></div>,
        target: payment.booking ? `Package #${payment.booking}` : payment.guide_request ? `Guide #${payment.guide_request}` : `Travel #${payment.service_booking}`,
        amount: `${payment.currency} ${payment.amount}`,
        provider: <div><Badge variant="outline">{payment.gateway}</Badge><p className="text-muted-foreground mt-1 text-xs">{payment.mode}</p></div>,
        status: <Badge variant={payment.status === 'SUCCESS' ? 'default' : 'secondary'}>{payment.status}</Badge>,
        created: new Date(payment.created_at).toLocaleString(),
      }))} />
  </div>;
}
