import { api } from "./client";

export interface BookingCreateRequest {
  trip_id: string;
  seats_reserved: number;
}

export interface BookingResponse {
  booking_id: string;
  trip_id: string;
  user_id: string;
  seats: number;
  seat_fare: number;
  total_amount: number;
  status: string; 
  booking_code: string;
  created_at: string;
  paid_at: string | null; 
  cancelled_at: string | null;
}

export async function createBooking(body: BookingCreateRequest): Promise<BookingResponse> {
  return api("booking/trip_confirm", {
    method: "POST",
    body,
    requireAuth: true,
  });
}

export async function getBookingDetails(bookingId: string): Promise<BookingResponse> {
  return api(`booking/booking/${bookingId}`, {
    method: "GET",
    requireAuth: true,
  });
}