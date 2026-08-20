import { AdminTable } from '@/components/common/admin-table';
import { PageHeader } from '@/components/layout/page-header';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { asList, coreGet } from '@/lib/api/server';

export const dynamic = 'force-dynamic';
interface PackageBooking { id: number; booking_reference: string; tour_package_title: string; tourist: number; status: string; total_price: string }
interface GuideRequest { id: number; reference: string; tourist_name: string; accepted_guide_name?: string; pickup_name: string; destination_name: string; status: string; final_fare?: string }
interface ServiceBooking { id: number; reference: string; tourist: number; status: string; total_price: string; offering_details: { title: string; service_type: string } }

export default async function BookingsPage() {
  const [packages, guideRequests, services] = await Promise.all([
    coreGet('/bookings/bookings/?page_size=100'), coreGet('/bookings/guide-requests/?page_size=100'), coreGet('/bookings/travel-service-bookings/?page_size=100'),
  ]);
  return <div><PageHeader title="Bookings" subtitle="Monitor package tours, on-demand guide requests, and travel reservations." />
    <Tabs defaultValue="guides"><TabsList><TabsTrigger value="guides">Guide requests</TabsTrigger><TabsTrigger value="packages">Packages</TabsTrigger><TabsTrigger value="services">Travel services</TabsTrigger></TabsList>
      <TabsContent value="guides"><AdminTable columns={[{ key: 'reference', label: 'Reference' }, { key: 'route', label: 'Route' }, { key: 'traveller', label: 'Traveller' }, { key: 'guide', label: 'Guide' }, { key: 'fare', label: 'Fare' }, { key: 'status', label: 'Status' }]} rows={asList<GuideRequest>(guideRequests).map((row) => ({ id: row.id, reference: row.reference, route: `${row.pickup_name} → ${row.destination_name}`, traveller: row.tourist_name, guide: row.accepted_guide_name || 'Searching', fare: row.final_fare ? `NPR ${row.final_fare}` : '—', status: <Badge variant="outline">{row.status}</Badge> }))} /></TabsContent>
      <TabsContent value="packages"><AdminTable columns={[{ key: 'reference', label: 'Reference' }, { key: 'package', label: 'Package' }, { key: 'traveller', label: 'Tourist ID' }, { key: 'total', label: 'Total' }, { key: 'status', label: 'Status' }]} rows={asList<PackageBooking>(packages).map((row) => ({ id: row.id, reference: row.booking_reference, package: row.tour_package_title, traveller: row.tourist, total: `NPR ${row.total_price}`, status: <Badge variant="outline">{row.status}</Badge> }))} /></TabsContent>
      <TabsContent value="services"><AdminTable columns={[{ key: 'reference', label: 'Reference' }, { key: 'service', label: 'Service' }, { key: 'traveller', label: 'Tourist ID' }, { key: 'total', label: 'Total' }, { key: 'status', label: 'Status' }]} rows={asList<ServiceBooking>(services).map((row) => ({ id: row.id, reference: row.reference, service: `${row.offering_details.service_type} • ${row.offering_details.title}`, traveller: row.tourist, total: `NPR ${row.total_price}`, status: <Badge variant="outline">{row.status}</Badge> }))} /></TabsContent>
    </Tabs>
  </div>;
}
