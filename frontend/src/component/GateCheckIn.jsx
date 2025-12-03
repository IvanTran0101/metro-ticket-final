import { useState, useEffect } from "react";
import { getStations, gateCheckIn } from "../api/journey";
import styles from "./Gate.module.css";

export default function GateCheckIn() {
    const [stations, setStations] = useState([]);
    const [stationId, setStationId] = useState("");
    const [code, setCode] = useState("");
    const [msg, setMsg] = useState(null);
    const [error, setError] = useState("");

    useEffect(() => {
        loadStations();
    }, []);

    async function loadStations() {
        try {
            const data = await getStations();
            setStations(data);
            if (data.length > 0) setStationId(data[0].station_id);
        } catch (err) {
            console.error(err);
        }
    }

    async function handleCheckIn(e) {
        e.preventDefault();
        setMsg(null);
        setError("");

        try {
            const res = await gateCheckIn(code, stationId);
            setMsg(res.message);
        } catch (err) {
            setError(err.message || "Check-in failed");
        }
    }

    return (
        <div className={styles.container}>
            <h2 className={styles.title}>🟢 Check-in Gate (Entry)</h2>

            <form onSubmit={handleCheckIn} className={styles.form}>
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

                <button type="submit" className={styles.button}>
                    Tap Card / Scan Code
                </button>
            </form>

            {msg && <div className={styles.success}>{msg}</div>}
            {error && <div className={styles.error}>{error}</div>}
        </div>
    );
}
