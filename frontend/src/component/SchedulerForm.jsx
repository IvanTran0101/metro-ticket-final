import { useState, useEffect, useMemo } from "react";
import { getNextTrains, getStations, checkFare, purchaseTicket } from "../api/journey";
import styles from "./SchedulerForm.module.css";
import TicketHistory from "./TicketHistory";

export default function SchedulerForm({ me, onLogout }) {
  const [stations, setStations] = useState([]);
  const [fromStation, setFromStation] = useState("");
  const [toStation, setToStation] = useState("");
  const [nextTrains, setNextTrains] = useState([]);
  const [loadingSchedule, setLoadingSchedule] = useState(false);
  const [loadingPurchase, setLoadingPurchase] = useState(false);
  const [error, setError] = useState("");
  const [fare, setFare] = useState(null);
  const [ticket, setTicket] = useState(null);
  const [ticketType, setTicketType] = useState("SINGLE");
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    loadStations();
  }, []);

  // Auto-fetch schedule when fromStation changes
  useEffect(() => {
    if (fromStation) {
      fetchSchedule(fromStation);
    }
  }, [fromStation]);

  // Auto-check price when both stations selected
  useEffect(() => {
    handleCheckPrice();
  }, [fromStation, toStation]);

  async function loadStations() {
    try {
      const data = await getStations();
      setStations(data);
      if (data.length > 0) {
        setFromStation(data[0].station_id);
        if (data.length > 1) {
          setToStation(data[1].station_id);
        }
      }
    } catch (err) {
      console.error("Failed to load stations", err);
      setError("Failed to load stations list");
    }
  }

  async function fetchSchedule(stationId) {
    setLoadingSchedule(true);
    setNextTrains([]);
    try {
      const res = await getNextTrains(stationId);
      setNextTrains(res.next_trains || []);
    } catch (err) {
      console.error("Schedule error:", err);
      // Don't show error to user immediately to keep UI clean, just log it
    } finally {
      setLoadingSchedule(false);
    }
  }

  async function handleCheckPrice() {
    if (!fromStation || !toStation) return;
    if (fromStation === toStation) {
      setFare(0);
      return;
    }
    try {
      const res = await checkFare(fromStation, toStation);
      setFare(res.standard_fare);
    } catch (e) {
      console.error(e);
      setFare(null);
    }
  }

  async function handleBuyTicket() {
    if (!fromStation || !toStation) {
      setError("Please select both stations");
      return;
    }
    if (fromStation === toStation) {
      setError("Origin and Destination cannot be the same");
      return;
    }

    setLoadingPurchase(true);
    setError("");
    setTicket(null);

    try {
      const res = await purchaseTicket(fromStation, toStation, ticketType);
      setTicket(res);

      // Rate Limiting: Keep loading state for 5 seconds to prevent spam
      // This disables the button
      setTimeout(() => {
        setLoadingPurchase(false);
      }, 5000);

    } catch (err) {
      console.error("Purchase error:", err);
      setError(err.message || "Purchase failed");
      setLoadingPurchase(false);
    }
  }

  const finalFare = useMemo(() => {
    let base = fare;

    // Fixed prices for passes
    if (ticketType === "DAY") base = 40000;
    else if (ticketType === "MONTH") base = 200000;
    else if (ticketType === "RETURN") base = fare ? fare * 2 : 0;
    else base = fare; // SINGLE

    if (base === null) return null;

    const type = me?.passenger_type || "STANDARD";
    if (type === "STUDENT") return base * 0.5;
    if (type === "ELDERLY") return 0;
    return base;
  }, [fare, me, ticketType]);

  const balanceFmt = useMemo(() => {
    return new Intl.NumberFormat('vi-VN').format(me?.balance || 0);
  }, [me]);

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.topBar}>
          <h2 className={styles.title}>Metro Station Hub</h2>
          <div className={styles.userInfo}>
            <div className={styles.balanceInfo}>
              <span className={styles.balanceLabel}>Balance:</span>
              <span className={styles.balanceValue}>{balanceFmt} VND</span>
            </div>
            {me?.passenger_type && (
              <div className={styles.roleBadge}>
                {me.passenger_type}
              </div>
            )}
            <button className={styles.logoutBtn} onClick={() => setShowHistory(true)} style={{ marginRight: '10px', background: '#2196F3' }}>My Tickets</button>
            <button className={styles.logoutBtn} onClick={onLogout}>Logout</button>
          </div>
        </div>

        <div className={styles.stationSelector}>
          <span className={styles.stationLabel}>Current Station:</span>
          <select
            className={styles.mainSelect}
            value={fromStation}
            onChange={(e) => setFromStation(e.target.value)}
          >
            {stations.map(s => (
              <option key={s.station_id} value={s.station_id}>{s.name}</option>
            ))}
          </select>
        </div>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.content}>
        {/* Left Column: Live Schedule */}
        <div className={`${styles.column} ${styles.leftColumn} `}>
          <h3 className={styles.sectionTitle}>🔴 Live Departures</h3>

          {loadingSchedule ? (
            <div className={styles.emptyState}>Loading schedule...</div>
          ) : nextTrains.length > 0 ? (
            <div className={styles.trainList}>
              {nextTrains.map((train, idx) => (
                <div key={idx} className={styles.trainItem}>
                  <div className={styles.trainHeader}>
                    <span>{train.line_name} <small style={{ opacity: 0.7 }}>({train.train_code})</small></span>
                    <span className={styles.minutes}>{train.minutes_left} min</span>
                  </div>
                  <div className={styles.trainTime}>
                    <span>To: {train.direction}</span>
                    <span>{train.departure_time}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.emptyState}>No upcoming trains found.</div>
          )}
        </div>

        {/* Right Column: Quick Ticket */}
        <div className={`${styles.column} ${styles.rightColumn} `}>
          <h3 className={styles.sectionTitle}>🎫 Quick Ticket</h3>

          <div className={styles.formGroup}>
            <label className={styles.label}>Destination</label>
            <select
              className={styles.select}
              value={toStation}
              onChange={(e) => setToStation(e.target.value)}
            >
              {stations.map(s => (
                <option key={s.station_id} value={s.station_id}>{s.name}</option>
              ))}
            </select>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>Ticket Type</label>
            <select
              className={styles.select}
              value={ticketType}
              onChange={(e) => setTicketType(e.target.value)}
            >
              <option value="SINGLE">Single Trip</option>
              <option value="RETURN">Return Trip</option>
              <option value="DAY">Day Pass (40k)</option>
              <option value="MONTH">Monthly Pass (200k)</option>
            </select>
          </div>

          {fare !== null && (
            <div className={styles.fareDisplay}>
              <div className={styles.fareRow}>
                <span>Base Price:</span>
                <span>
                  {new Intl.NumberFormat('vi-VN').format(
                    (ticketType === "DAY") ? 40000 :
                      (ticketType === "MONTH") ? 200000 :
                        (ticketType === "RETURN") ? (fare * 2) : fare
                  )} VND
                </span>
              </div>
              {me?.passenger_type && me.passenger_type !== "STANDARD" && (
                <div className={`${styles.fareRow} ${styles.discountRow} `}>
                  <span>{me.passenger_type} Price:</span>
                  <span className={styles.finalPrice}>{new Intl.NumberFormat('vi-VN').format(finalFare)} VND</span>
                </div>
              )}
              {!me?.passenger_type || me.passenger_type === "STANDARD" ? (
                <div className={`${styles.fareRow} ${styles.totalRow} `}>
                  <span>Total:</span>
                  <span className={styles.finalPrice}>{new Intl.NumberFormat('vi-VN').format(finalFare)} VND</span>
                </div>
              ) : null}
            </div>
          )}

          <button
            className={styles.button}
            onClick={handleBuyTicket}
            disabled={loadingPurchase || fare === null}
          >
            {loadingPurchase ? "Processing..." : "Purchase Ticket"}
          </button>

          {ticket && (
            <div className={styles.successBox}>
              <div className={styles.successTitle}>Payment Successful!</div>
              <span className={styles.ticketCode}>{ticket.journey_code}</span>
              <p>Please save this code for Check-in</p>
            </div>
          )}
        </div>
      </div>
      {showHistory && <TicketHistory onClose={() => setShowHistory(false)} />}
    </div>
  );
}