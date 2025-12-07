import { useState, useEffect } from "react";
import { getStations, gateCheckOut, payPenalty } from "../api/journey";
import styles from "./Gate.module.css";

export default function GateCheckOut() {
    const [stations, setStations] = useState([]);
    const [stationId, setStationId] = useState("");
    const [code, setCode] = useState("");
    const [msg, setMsg] = useState(null);
    const [error, setError] = useState("");
    const [penalty, setPenalty] = useState(null);

    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadStations();
    }, []);

    async function loadStations() {
        try {
            const data = await getStations();
            setStations(data);
            if (data.length > 0) setStationId(data[data.length - 1]?.station_id || data[0].station_id);
        } catch (err) {
            console.error(err);
            setError("Failed to load stations. Please try again.");
        }
    }

    async function handleCheckOut(e) {
        e.preventDefault();
        setMsg(null);
        setError("");
        setPenalty(null);
        setLoading(true);

        try {
            const res = await gateCheckOut(code, stationId);
            setMsg(res.message);
        } catch (err) {
            // Check if it is a penalty error (402)
            if (err.status === 402) {
                setPenalty({
                    amount: err.detail?.penalty_amount,
                    reason: err.detail?.message
                });
            } else {
                setError(err.message || "Check-out failed");
            }
        } finally {
            setLoading(false);
        }
    }

    async function handlePayPenalty() {
        setLoading(true);
        try {
            const res = await payPenalty(code, penalty.amount);
            setPenalty(null);
            setMsg(res.message);
        } catch (err) {
            setError(err.message || "Penalty payment failed");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h2 className={styles.title}>🔴 Check-out Gate (Exit)</h2>
            </div>

            <form onSubmit={handleCheckOut} className={styles.form}>
                <div className={styles.field}>
                    <label>Current Station</label>
                    <select
                        value={stationId}
                        onChange={(e) => setStationId(e.target.value)}
                        className={styles.select}
                    >
                        {stations.map(s => (
                            <option key={s.station_id} value={s.station_id}>
                                {s.name}
                            </option>
                        ))}
                    </select>
                </div>

                <div className={styles.field}>
                    <label>Journey Code</label>
                    <input
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        className={styles.input}
                        placeholder="Enter 6-digit code"
                        required
                    />
                </div>

                <button type="submit" className={styles.button} disabled={loading}>
                    {loading ? "Processing..." : "Tap Card / Scan Code"}
                </button>
            </form>

            {penalty && (
                <div className={styles.penaltyBox}>
                    <h3>⚠️ Penalty Due</h3>
                    <p>{penalty.reason}</p>
                    <span className={styles.penaltyAmount}>{penalty.amount?.toLocaleString()} VND</span>
                    <button onClick={handlePayPenalty} className={`${styles.button} ${styles.payBtn}`} disabled={loading}>
                        {loading ? "Processing..." : "Pay Penalty & Exit"}
                    </button>
                </div>
            )}

            {msg && <div className={styles.success}>{msg}</div>}
            {error && <div className={styles.error}>{error}</div>}
        </div>
    );
}
