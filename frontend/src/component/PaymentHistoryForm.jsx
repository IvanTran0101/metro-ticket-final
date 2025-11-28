import { useState, useEffect } from "react";
import styles from "./PaymentHistoryForm.module.css";

export default function PaymentHistoryForm({ onBackToHome }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    // Placeholder for fetching payment history from API
    // TODO: Implement API call to fetch payment history
    setLoading(false);
    // For now, show empty state
    setHistory([]);
  }, []);

  return (
    <div className={styles.card}>
      <h2 className={styles.title}>Payment History</h2>

      {error && <div className={styles.error}>{error}</div>}

      {loading ? (
        <div className={styles.loading}>Loading payment history...</div>
      ) : history.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>📜</div>
          <p>No payment history found</p>
          <p className={styles.emptyDesc}>Your completed transactions will appear here</p>
        </div>
      ) : (
        <div className={styles.historyTable}>
          <table>
            <thead>
              <tr>
                <th>Payment ID</th>
                <th>Booking Code</th>
                <th>Amount</th>
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item) => (
                <tr key={item.payment_id}>
                  <td>{item.payment_id}</td>
                  <td>{item.booking_code}</td>
                  <td>{Number(item.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })} VND</td>
                  <td>{new Date(item.created_at).toLocaleString()}</td>
                  <td>
                    <span className={`${styles.status} ${styles[item.status?.toLowerCase() || 'pending']}`}>
                      {item.status || 'Unknown'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
