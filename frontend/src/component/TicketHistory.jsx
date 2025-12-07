import { useState, useEffect } from "react";
import { getJourneyHistory, getMyTickets } from "../api/journey";
import styles from "./TicketHistory.module.css";

export default function TicketHistory({ onClose }) {
    const [activeTab, setActiveTab] = useState("wallet"); // wallet | history
    const [history, setHistory] = useState([]);
    const [tickets, setTickets] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            setLoading(true);
            try {
                const [hData, tData] = await Promise.all([
                    getJourneyHistory(),
                    getMyTickets()
                ]);
                setHistory(hData || []);
                setTickets(tData || []);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    return (
        <div className={styles.overlay}>
            <div className={styles.modal}>
                <div className={styles.header}>
                    <div className={styles.tabs}>
                        <button
                            className={`${styles.tabBtn} ${activeTab === 'wallet' ? styles.activeTab : ''}`}
                            onClick={() => setActiveTab('wallet')}
                        >
                            My Wallet
                        </button>
                        <button
                            className={`${styles.tabBtn} ${activeTab === 'history' ? styles.activeTab : ''}`}
                            onClick={() => setActiveTab('history')}
                        >
                            Journey History
                        </button>
                    </div>
                    <button onClick={onClose} className={styles.closeBtn}>×</button>
                </div>

                <div className={styles.content}>
                    {loading ? (
                        <div className={styles.loading}>Loading...</div>
                    ) : (
                        <>
                            {activeTab === 'wallet' && (
                                <WalletView tickets={tickets} />
                            )}
                            {activeTab === 'history' && (
                                <HistoryView history={history} />
                            )}
                        </>
                    )}
                </div>
                <div className={styles.footer}>
                    <button onClick={onClose} className={styles.backBtn}>Back</button>
                </div>
            </div>
        </div>
    );
}

function WalletView({ tickets }) {
    if (tickets.length === 0) return <div className={styles.empty}>No tickets found</div>;

    return (
        <table className={styles.table}>
            <thead>
                <tr>
                    <th>Code</th>
                    <th>Type</th>
                    <th>Valid Route</th>
                    <th>Trips Left</th>
                    <th>Valid Until</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {tickets.map((t) => (
                    <tr key={t.ticket_id}>
                        <td><div className={styles.code}>{t.ticket_code}</div></td>
                        <td>{t.ticket_type}</td>
                        <td>
                            {t.ticket_type === 'SINGLE' || t.ticket_type === 'RETURN' ? (
                                <span className={styles.routeText}>
                                    {t.origin_station_id} ↔ {t.destination_station_id}
                                </span>
                            ) : (
                                <span className={styles.routeText}>Unlimited</span>
                            )}
                        </td>
                        <td>
                            {t.remaining_trips === null ? "∞" : t.remaining_trips} / {t.max_trips}
                        </td>
                        <td>
                            {t.valid_until ? new Date(t.valid_until).toLocaleDateString() : 'N/A'}
                        </td>
                        <td>
                            <span className={`${styles.status} ${styles[t.status]}`}>
                                {t.status}
                            </span>
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}

function HistoryView({ history }) {
    if (history.length === 0) return <div className={styles.empty}>No journeys found</div>;

    return (
        <table className={styles.table}>
            <thead>
                <tr>
                    <th>Journey Code</th>
                    <th>Route</th>
                    <th>Time</th>
                    <th>Fee/Penalty</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {history.map((h, i) => (
                    <tr key={i}>
                        <td>
                            <div className={styles.code}>{h.journey_code}</div>
                        </td>
                        <td>
                            <div className={styles.route}>
                                <span>{h.check_in_station_id}</span>
                                <span>➝</span>
                                <span>{h.check_out_station_id || "..."}</span>
                            </div>
                        </td>
                        <td>
                            <div>{new Date(h.check_in_time).toLocaleString()}</div>
                            {h.check_out_time && (
                                <div className={styles.subTime}>
                                    Out: {new Date(h.check_out_time).toLocaleTimeString()}
                                </div>
                            )}
                        </td>
                        <td>
                            {h.penalty_amount > 0 ? (
                                <span className={styles.penalty}>-{h.penalty_amount.toLocaleString()}</span>
                            ) : (
                                <span>{h.fare_amount?.toLocaleString()}</span>
                            )}
                        </td>
                        <td>
                            <span className={`${styles.status} ${styles[h.status]}`}>
                                {h.status}
                            </span>
                            {h.penalty_reason && (
                                <div className={styles.reason}>{h.penalty_reason}</div>
                            )}
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}
