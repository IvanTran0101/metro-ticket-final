import { client } from './client';

// --- Ticket Machine ---
export async function getStations() {
    // Assuming scheduler service has an endpoint for stations, 
    // or we hardcode them if the API is missing. 
    // Based on previous context, we might need to fetch lines/stations.
    // For now, let's try to fetch from scheduler if possible, or return a hardcoded list if the endpoint is complex.
    // Checking previous context: `scheduler_service` has `/lines` and `/lines/{line_id}/stations`.
    // Let's assume we want stations for Line 1 (L1) for simplicity, or fetch all.
    try {
        const res = await client.get('/scheduler/stations?line_id=L01');
        return res;
    } catch (e) {
        console.warn("Could not fetch stations, using fallback", e);
        return [
            { station_id: "S01", name: "Ben Thanh", distance_km: 0 },
            { station_id: "S02", name: "Nha Hat Lon", distance_km: 0.6 },
            { station_id: "S03", name: "Ba Son", distance_km: 2.3 },
            { station_id: "S13", name: "Suoi Tien", distance_km: 19.7 },
        ];
    }
}

export async function purchaseTicket(fromStation, toStation) {
    return client.post('/booking/ticket/purchase', {
        from_station: fromStation,
        to_station: toStation,
        passenger_type: "STANDARD" // Backend will override based on user profile
    });
}

// --- Gate Simulator ---
export async function gateCheckIn(journeyCode, stationId) {
    return client.post('/booking/gate/check-in', {
        journey_code: journeyCode,
        station_id: stationId
    });
}

export async function gateCheckOut(journeyCode, stationId) {
    return client.post('/booking/gate/check-out', {
        journey_code: journeyCode,
        station_id: stationId
    });
}

export async function payPenalty(journeyCode, amount) {
    return client.post('/booking/ticket/pay-penalty', {
        journey_code: journeyCode,
        amount: amount,
        auto_topup: true
    });
}
