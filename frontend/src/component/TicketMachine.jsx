import { useState, useEffect } from "react";
import { getStations, purchaseTicket } from "../api/journey";
import styles from "./TicketMachine.module.css";

export default function TicketMachine() {
    const [stations, setStations] = useState([]);
    const [fromStation, setFromStation] = useState("");
    const [toStation, setToStation] = useState("");
    const [ticket, setTicket] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        loadStations();
    }, []);

    async function loadStations() {
        try {
            const data = await getStations();
            setStations(data);
            if (data.length > 0) {
                setFromStation(data[0].station_id);
                setToStation(data[1]?.station_id || data[0].station_id);
            }
        } catch (err) {
            console.error("Failed to load stations", err);
        }
    }

    async function handlePurchase(e) {
        e.preventDefault();
        if (fromStation === toStation) {
            setError("Origin and Destination cannot be the same");
            return;
        }

        setLoading(true);
        setError("");
        setTicket(null);

        try {
            const res = await purchaseTicket(fromStation, toStation);
            setTicket(res);
        } catch (err) {
            setError(err.message || "Purchase failed");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className={styles.container}>
            <h2 className={styles.title}>🎟️ Ticket Vending Machine</h2>

            <div className={styles.grid}>
                <form onSubmit={handlePurchase} className={styles.form}>
                    <div className={styles.field}>
                        <label>From Station</label>
                        <select
                            value={fromStation}
                            onChange={(e) => setFromStation(e.target.value)}
                            className={styles.select}
                        >
                            {stations.map(s => (
                                <option key={s.station_id} value={s.station_id}>
                                    {s.name} (ID: {s.station_id})
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className={styles.field}>
                        <label>To Station</label>
                        <select
                            value={toStation}
                            onChange={(e) => setToStation(e.target.value)}
                            className={styles.select}
                        >
                            {stations.map(s => (
                                <option key={s.station_id} value={s.station_id}>
                                    {s.name} (ID: {s.station_id})
                                </option>
                            ))}
                        </select>
                    </div>

                    <button type="submit" disabled={loading} className={styles.button}>
                        {loading ? "Processing..." : "Purchase Ticket"}
                    </button>
                </form>

                <div className={styles.resultArea}>
                    {error && <div className={styles.error}>{error}</div>}

                    {ticket && (
                        <div className={styles.ticket}>
                            <h3>✅ Ticket Purchased!</h3>
                            <div className={styles.codeBox}>
                                <span className={styles.label}>JOURNEY CODE</span>
                                <span className={styles.code}>{ticket.journey_code}</span>
                            </div>
                            <div className={styles.details}>
                                <p>Fare: <strong>{ticket.fare_amount?.toLocaleString()} VND</strong></p>
                                <p>{ticket.message}</p>
                            </div>
                            <p className={styles.hint}>Please save this code for Check-in/Check-out</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
