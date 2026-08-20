import { Hotel, Plane, Bus } from 'lucide-react';

import { AdminTable } from '@/components/common/admin-table';
import { PageHeader } from '@/components/layout/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { createOfferingAction } from '@/lib/actions/platform';
import { asList, coreGet } from '@/lib/api/server';

export const dynamic = 'force-dynamic';
interface OfferingRow { id: number; service_type: string; provider_name: string; title: string; location: string; origin: string; destination: string; unit_price: string; currency: string; capacity: number; available_units: number; is_active: boolean }

export default async function InventoryPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const offerings = asList<OfferingRow>(await coreGet('/bookings/travel-offerings/?page_size=100'));
  const { error } = await searchParams;
  return <div><PageHeader title="Travel inventory" subtitle="Local thesis-demo inventory for hotels, flights, and buses." />
    {error && <p className="bg-destructive/10 text-destructive mb-4 rounded-md p-3 text-sm">{error}</p>}
    <Card className="mb-6"><CardHeader><CardTitle>Add availability</CardTitle><CardDescription>For hotels use location; for flights and buses use origin and destination.</CardDescription></CardHeader><CardContent>
      <form action={createOfferingAction} className="grid gap-3 md:grid-cols-3 lg:grid-cols-4">
        <div className="space-y-1"><Label htmlFor="service_type">Type</Label><select id="service_type" name="service_type" className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"><option>HOTEL</option><option>FLIGHT</option><option>BUS</option></select></div>
        <div className="space-y-1"><Label htmlFor="provider_name">Provider</Label><Input id="provider_name" name="provider_name" required /></div>
        <div className="space-y-1"><Label htmlFor="title">Title</Label><Input id="title" name="title" required /></div>
        <div className="space-y-1"><Label htmlFor="location">Hotel location</Label><Input id="location" name="location" /></div>
        <div className="space-y-1"><Label htmlFor="origin">Origin</Label><Input id="origin" name="origin" /></div>
        <div className="space-y-1"><Label htmlFor="destination">Destination</Label><Input id="destination" name="destination" /></div>
        <div className="space-y-1"><Label htmlFor="unit_price">Price NPR</Label><Input id="unit_price" name="unit_price" type="number" min="1" required /></div>
        <div className="space-y-1"><Label htmlFor="capacity">Capacity</Label><Input id="capacity" name="capacity" type="number" min="1" required /></div>
        <Button className="self-end"><Hotel className="size-4" /> Add service</Button>
      </form>
    </CardContent></Card>
    <AdminTable columns={[{ key: 'service', label: 'Service' }, { key: 'provider', label: 'Provider' }, { key: 'route', label: 'Location / route' }, { key: 'price', label: 'Price' }, { key: 'available', label: 'Availability' }, { key: 'status', label: 'Status' }]}
      rows={offerings.map((offering) => ({
        id: offering.id,
        service: <span className="flex items-center gap-2">{offering.service_type === 'HOTEL' ? <Hotel className="size-4" /> : offering.service_type === 'FLIGHT' ? <Plane className="size-4" /> : <Bus className="size-4" />}<span>{offering.title}</span></span>,
        provider: offering.provider_name,
        route: offering.service_type === 'HOTEL' ? offering.location : `${offering.origin} → ${offering.destination}`,
        price: `${offering.currency} ${offering.unit_price}`,
        available: `${offering.available_units} / ${offering.capacity}`,
        status: <Badge variant={offering.is_active ? 'default' : 'secondary'}>{offering.is_active ? 'Active' : 'Hidden'}</Badge>,
      }))} />
  </div>;
}
