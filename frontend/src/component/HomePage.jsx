import { useState, useEffect } from "react";
import { getAccountMe } from "../api/account";
import { logout } from "../api/auth";
import styles from "./HomePage.module.css";

export default function HomePage({ onLoggedOut, onStartBooking, onViewPaymentHistory }) {
  const [me, setMe] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const data = await getAccountMe();
        setMe(data);
      } catch (e) {
        setError("Failed to load profile. Please re-login.");
      }
    })();
  }, []);

  function handleLogout() {
    logout();
    onLoggedOut?.();
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h1 className={styles.title}>Metro Ticket Booking System</h1>
          <p className={styles.subtitle}>Welcome to your ticket booking portal</p>
        </div>

        {error && <div className={styles.error}>{error}</div>}

        {me && (
          <div className={styles.profile}>
            <div className={styles.profileItem}>
              <span className={styles.label}>Name:</span>
              <span className={styles.value}>{me.name}</span>
            </div>
            <div className={styles.profileItem}>
              <span className={styles.label}>Email:</span>
              <span className={styles.value}>{me.email}</span>
            </div>
            <div className={styles.profileItem}>
              <span className={styles.label}>Phone Number:</span>
              <span className={styles.value}>{me.phone_number}</span>
            </div>
            <div className={styles.profileItem}>
              <span className={styles.label}>Balance:</span>
              <span className={styles.balance}>
                {Number(me.balance || 0).toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}{" "}
                VND
              </span>
            </div>
          </div>
        )}

        <div className={styles.actions}>
          <h2>What would you like to do?</h2>

          <div className={styles.buttonGrid}>
            <button
              className={`${styles.button} ${styles.primary}`}
              onClick={onStartBooking}
            >
              <div className={styles.buttonIcon}>🎫</div>
              <div className={styles.buttonTitle}>Start Booking</div>
              <div className={styles.buttonDesc}>Search and book metro tickets</div>
            </button>

            <button
              className={`${styles.button} ${styles.secondary}`}
              onClick={onViewPaymentHistory}
            >
              <div className={styles.buttonIcon}>📋</div>
              <div className={styles.buttonTitle}>Payment History</div>
              <div className={styles.buttonDesc}>View your past transactions</div>
            </button>
          </div>
        </div>

        <div className={styles.footer}>
          <button
            className={`${styles.button} ${styles.logout}`}
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}
