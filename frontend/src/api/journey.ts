import { api } from "./client";

export interface Station {
    station_id: string;
    name: string;
}

export interface TicketResponse {
    journey_code: string;
    fare_amount: number;
    message: string;
}

export interface FareResponse {
    standard_fare: number;
}

export async function getStations(): Promise<Station[]> {
    try {
        return await api<Station[]>('/scheduler/stations');
    } catch (e) {
        console.warn("Could not fetch stations, using fallback", e);
        return [
            { station_id: "S01", name: "Ben Thanh" },
            { station_id: "S02", name: "Nha Hat Lon" },
            { station_id: "S03", name: "Ba Son" },
            { station_id: "S13", name: "Suoi Tien" },
        ];
    }
}

export async function purchaseTicket(fromStation: string, toStation: string): Promise<TicketResponse> {
    return api<TicketResponse>('/booking/ticket/purchase', {
        method: 'POST',
        body: {
            from_station: fromStation,
            to_station: toStation,
            passenger_type: "STANDARD"
        }
    });
}

export async function gateCheckIn(journeyCode: string, stationId: string): Promise<any> {
    return api('/booking/gate/check-in', {
        method: 'POST',
        body: {
            journey_code: journeyCode,
            station_id: stationId
        },
        requireAuth: false
    });
}

export async function gateCheckOut(journeyCode: string, stationId: string): Promise<any> {
    return api('/booking/gate/check-out', {
        method: 'POST',
        body: {
            journey_code: journeyCode,
            station_id: stationId
        },
        requireAuth: false
    });
}

export async function payPenalty(journeyCode: string, amount: number): Promise<any> {
    return api('/booking/ticket/pay-penalty', {
        method: 'POST',
        body: {
            journey_code: journeyCode,
            amount: amount,
            auto_topup: true
        },
        requireAuth: false
    });
}

export async function getAccountInfo(): Promise<any> {
    return api('/account/me');
}

export async function checkFare(fromStation: string, toStation: string): Promise<FareResponse> {
    return api<FareResponse>('/scheduler/routes/search', {
        method: 'POST',
        body: {
            from_station: fromStation,
            to_station: toStation
        }
    });
}

export async function getNextTrains(stationId: string): Promise<any> {
    return api(`/scheduler/stations/${stationId}/next-trains`);
}
