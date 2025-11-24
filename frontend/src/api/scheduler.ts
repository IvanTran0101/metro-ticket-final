import { api } from "./client";

export interface TripResponse {
  trip_id: string;
  from_station_name: string;
  to_station_name: string;
  date_departure: string; 
  departure_time: string;
  capacity: number;
  remaining_seats: number;
  status: string;
  route_name: string;
  fare_per_seat: number;
}

export async function getTripDetails(tripId: string): Promise<TripResponse> {
  return api(`/internal/get/route/trip/${tripId}`, {
    method: "GET",
    requireAuth: true,
  });
}
    