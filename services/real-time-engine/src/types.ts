/** Shared types mirroring the Redis event contract (see docs/api-contracts.md). */

export interface AuthedUser {
  /** Numeric for Django's integer pks; string tolerated for UUID pks. */
  userId: number | string;
  role?: string;
}

/** Base shape of every event Django publishes on the Redis bus. */
export interface DomainEvent {
  event: string;
  [key: string]: unknown;
}

export interface BookingEvent extends DomainEvent {
  booking_id: number;
  booking_reference: string;
  status: string;
  tourist_id: number;
  assigned_guide_id: number | null;
}

export interface PaymentEvent extends DomainEvent {
  payment_id: number;
  user_id: number;
  booking_id: number | null;
  status: string;
}

export interface PermitEvent extends DomainEvent {
  permit_id: number;
  applicant_id: number;
  status: string;
}

export interface NotificationEvent extends DomainEvent {
  notification_id: number;
  user_id: number;
  kind: string;
  title: string;
}

/** Client→server payloads. */
export interface ChatJoinPayload {
  room: string;
}
export interface ChatMessagePayload {
  room: string;
  body: string;
}
export interface AvailabilityPayload {
  available: boolean;
}

export const CHANNELS = {
  USER: 'guideu:user.events',
  BOOKING: 'guideu:booking.events',
  PAYMENT: 'guideu:payment.events',
  PERMIT: 'guideu:permit.events',
  NOTIFICATION: 'guideu:notification.events',
  REVIEW: 'guideu:review.events',
} as const;
