import { useState, useEffect } from "react";
import { getStations, purchaseTicket, getAccountInfo, checkFare, getNextTrains } from "../api/journey";
import styles from "./TicketMachine.module.css";

export default function TicketMachine({ onPurchaseSuccess }) {
    const [stations, setStations] = useState([]);
    const [fromStation, setFromStation] = useState("");
    const [toStation, setToStation] = useState("");
    const [ticket, setTicket] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    // New State for UI Updates
    const [balance, setBalance] = useState(null);
    const [fare, setFare] = useState(null);
    const [showNextTrains, setShowNextTrains] = useState(false);
    const [nextTrains, setNextTrains] = useState([]);

    useEffect(() => {
        loadStations();
        loadBalance();
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

    async function loadBalance() {
        try {
            const data = await getAccountInfo();
            setBalance(data.balance);
        } catch (err) {
            console.warn("Failed to load balance", err);
        }
    }

    async function handleCheckPrice(e) {
        e.preventDefault();
        if (fromStation === toStation) {
            setError("Origin and Destination cannot be the same");
            return;
        }
        setError("");
        setFare(null);

        try {
            const res = await checkFare(fromStation, toStation);
            setFare(res.standard_fare);
        } catch (err) {
            setError("Could not calculate fare");
        }
    }

    async function handleNextTrains(e) {
        e.preventDefault();
        setShowNextTrains(!showNextTrains);
        if (!showNextTrains) {
            // Fetch when opening
            try {
                const res = await getNextTrains(fromStation);
                setNextTrains(res.trains || []);
            } catch (err) {
                console.error("Failed to fetch next trains", err);
            }
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
            loadBalance(); // Refresh local balance
            onPurchaseSuccess?.(); // Refresh global balance
        } catch (err) {
            setError(err.message || "Purchase failed");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className={styles.container}>
            <h2 className={styles.title}>🎟️ Ticket Vending Machine</h2>

            {balance !== null && (
                <div className={styles.balanceBox}>
                    Balance: <strong>{balance.toLocaleString()} VND</strong>
                </div>
            )}

            <div className={styles.grid}>
                <form className={styles.form}>
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

                    <div className={styles.buttonGroup}>
                        <button onClick={handleCheckPrice} className={styles.secondaryButton}>
                            Check Price
                        </button>
                        <button onClick={handleNextTrains} className={styles.secondaryButton}>
                            Next Trains
                        </button>
                    </div>

                    {fare !== null && (
                        <div className={styles.fareDisplay}>
                            STANDARD FARE: <strong>{fare.toLocaleString()} VND</strong>
                        </div>
                    )}

                    <button onClick={handlePurchase} disabled={loading} className={styles.button}>
                        {loading ? "Processing..." : "Purchase Ticket"}
                    </button>
                </form>

                <div className={styles.resultArea}>
                    {error && <div className={styles.error}>{error}</div>}

                    {showNextTrains && (
                        <div className={styles.nextTrainsBox}>
                            <h3>🚆 Next Trains from {fromStation}</h3>
                            {nextTrains.length === 0 ? (
                                <p>No trains found.</p>
                            ) : (
                                <ul>
                                    {nextTrains.map(t => (
                                        <li key={t.trip_id}>
                                            {t.departure_time} - {t.station_name} (Route {t.route_id})
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    )}

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
