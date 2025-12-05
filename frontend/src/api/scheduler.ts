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


  return api<TripResponse[]>('/route/trips', {
    method: "POST",
    body: params,
    requireAuth: true,
  });
}

export interface NextTrainInfo {
  line_name: string;
  direction: string;
  departure_time: string;
  minutes_left: number;
  train_code?: string;
}

export interface StationScheduleResponse {
  station_id: string;
  station_name: string;
  current_time: string;
  next_trains: NextTrainInfo[];
}

export async function getNextTrains(stationId: string): Promise<StationScheduleResponse> {
  return api<StationScheduleResponse>(`/scheduler/stations/${stationId}/next-trains`, {
    method: "GET",
    requireAuth: true,
  });
}