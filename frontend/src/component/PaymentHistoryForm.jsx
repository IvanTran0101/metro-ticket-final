import { useState, useEffect } from "react";
import { getPaymentHistory } from "../api/payment"; 
import styles from "./PaymentHistoryForm.module.css";

export default function PaymentHistoryForm({ onBackToHome }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchHistory() {
      try {
        setLoading(true);
        const data = await getPaymentHistory(); 
        setHistory(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error(err);
        setError("Failed to load payment history");
      } finally {
        setLoading(false);
      }
    }

    fetchHistory();
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
                <th>Booking ID</th>
                <th>Amount</th>
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item) => (
                <tr key={item.payment_id}>
                  <td>{item.payment_id}</td>
                  <td>{item.booking_id}</td>
                  <td>
                    {item.amount.toLocaleString(undefined, {
                      minimumFractionDigits: 0,
                      maximumFractionDigits: 0,
                    })}{" "}
                    VND
                  </td>
                  <td>{new Date(item.complete_at).toLocaleString()}</td>
                  <td>
                    <span
                      className={`${styles.status} ${
                        styles[item.status?.toLowerCase()] || ""
                      }`}
                    >
                      {item.status || "Unknown"}
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
