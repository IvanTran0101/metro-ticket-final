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
        console.error("Failed to fetch stations", e);
        throw e;
    }
}

export async function purchaseTicket(fromStation: string, toStation: string, ticketType: string = "SINGLE"): Promise<TicketResponse> {
    return api<TicketResponse>('/booking/ticket/purchase', {
        method: 'POST',
        body: {
            from_station: fromStation,
            to_station: toStation,
            ticket_type: ticketType,
            passenger_type: "STANDARD"
        }
    });
}

export async function getJourneyHistory(): Promise<any[]> {
    return api<any[]>('/booking/history');
}

export async function getMyTickets(): Promise<any[]> {
    return api<any[]>('/booking/tickets');
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
    return api('/booking/gate/pay-penalty', {
        method: 'POST',
        body: { journey_code: journeyCode, amount },
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
