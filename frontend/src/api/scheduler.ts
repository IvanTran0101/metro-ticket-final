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

export interface SearchTripsParams {
  from_station?: string;
  to_station?: string;
  date?: string;
}

export async function searchTrips(params: SearchTripsParams): Promise<TripResponse[]> {
  const { from_station, to_station, date } = params;

  const q: Record<string, string> = {};
  if (from_station) q.from_station = String(from_station).trim();
  if (to_station) q.to_station = String(to_station).trim();
  if (date && date.trim()) q.date = String(date).trim();

  return api<TripResponse[]>('/route/trips', {
    method: "GET",
    query: q, 
    requireAuth: true,
  });
}