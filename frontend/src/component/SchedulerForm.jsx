import { useState } from "react";
import { searchTrips } from "../api/scheduler";
import { createBooking } from "../api/booking";
import { ApiError } from "../api/client";
import styles from "./SchedulerForm.module.css";

export default function SchedulerForm({ onBookingConfirmed }) {
  const [fromStation, setFromStation] = useState("");
  const [toStation, setToStation] = useState("");
  const [date, setDate] = useState(""); 
  const [trips, setTrips] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [seats, setSeats] = useState(1);
  const [booking, setBooking] = useState(null);

  async function handleSearch(e) {
    e?.preventDefault();
    setError("");
    setTrips([]);
    setSelected(null);
    setBooking(null);

    setLoading(true);
    try {
      const res = await searchTrips({ 
        from_station: fromStation.value, 
        to_station: toStation.value, 
        date: date.value || undefined 
      });
      console.log(res)
      const payload = Array.isArray(res) ? res : (res?.data || res?.results || res?.trips || []);
      
      setTrips(res);
      if (!payload || (Array.isArray(payload) && payload.length === 0)) {
        setError("No trips found for the given criteria");
      }
    } catch (err) {
      console.error("Search error:", err);
      if (err instanceof ApiError) {
        const detail = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
        setError(`Server error ${err.status}: ${detail}`);
      } else {
        setError(err?.message || "Failed to search trips");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirm(e) {
    e?.preventDefault();
    setError("");
    
    if (!selected) {
      setError("Please select a trip first");
      return;
    }
    
    if (seats < 1 || seats > selected.remaining_seats) {
      setError("Invalid seat count");
      return;
    }

    setLoading(true);
    try {
      const res = await createBooking({ 
        trip_id: selected.trip_id, 
        seats_reserved: Number(seats) 
      });
      setBooking(res);
      setError("");
      // inform parent to navigate to payment with booking data
      try {
        onBookingConfirmed?.(res);
      } catch (e) {
        // ignore
      }
    } catch (err) {
      console.error("Booking error:", err);
      if (err instanceof ApiError) {
        const detail = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
        setError(`Server error ${err.status}: ${detail}`);
      } else {
        setError(err?.message || "Booking failed");
      }
    } finally {
      setLoading(false);
    }
  }

  function handleSelectTrip(trip) {
    setSelected(trip);
    setBooking(null);
    setError("");
    setSeats(1);
  }

  return (
    <div className={styles.card}>
      <h2 className={styles.title}>Trip Booking</h2>

      {error && <div className={styles.error}>{error}</div>}

      <h3>1. Search Trips</h3>

      <form onSubmit={handleSearch}>
        <label className={styles.label}>
          From Station
          <input 
            className={styles.input}
            value={fromStation} 
            onChange={(e) => setFromStation(e.target.value)} 
            placeholder="Enter departure station"
            required 
          />
        </label>

        <label className={styles.label}>
          To Station
          <input 
            className={styles.input}
            value={toStation} 
            onChange={(e) => setToStation(e.target.value)} 
            placeholder="Enter arrival station"
            required 
          />
        </label>

        <label className={styles.label}>
          Date (optional)
          <input 
            className={styles.input}
            type="date" 
            value={date} 
            onChange={(e) => setDate(e.target.value)} 
          />
        </label>

        <button className={styles.button} type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search Trips"}
        </button>
      </form>

      {trips.length > 0 && (
        <>
          <h3>2. Available Trips ({trips.length} found)</h3>
          <div className={styles.tripList}>
            {trips.map((trip) => (
              <div 
                key={trip.trip_id} 
                className={`${styles.tripCard} ${selected?.trip_id === trip.trip_id ? styles.selectedTrip : ''}`}
                onClick={() => handleSelectTrip(trip)}
              >
                <div className={styles.tripHeader}>
                  <strong>{trip.route_name}</strong>
                  {trip.brand && <span className={styles.brand}>{trip.brand}</span>}
                </div>
                
                <div className={styles.tripRoute}>
                  {trip.from_station_name} → {trip.to_station_name}
                </div>
                
                <div className={styles.tripDetails}>
                  <span>📅 {trip.date_departure}</span>
                  <span>🕐 {trip.departure_time}</span>
                </div>
                
                <div className={styles.tripDetails}>
                  <span>💺 {trip.remaining_seats} / {trip.capacity} seats</span>
                  <span>💰 {new Intl.NumberFormat('vi-VN').format(trip.fare_per_seat)} VND</span>
                </div>

                {selected?.trip_id === trip.trip_id && (
                  <div className={styles.selectedBadge}>✓ Selected</div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {selected && (
        <>
          <h3>3. Confirm Booking</h3>
          
          <div className={styles.summaryCard}>
            <div className={styles.summaryRow}>
              <span>Route:</span>
              <strong>{selected.route_name}</strong>
            </div>
            <div className={styles.summaryRow}>
              <span>From - To:</span>
              <strong>{selected.from_station_name} → {selected.to_station_name}</strong>
            </div>
            <div className={styles.summaryRow}>
              <span>Departure:</span>
              <strong>{selected.date_departure} at {selected.departure_time}</strong>
            </div>
            <div className={styles.summaryRow}>
              <span>Available Seats:</span>
              <strong>{selected.remaining_seats} / {selected.capacity}</strong>
            </div>
            <div className={styles.summaryRow}>
              <span>Price per Seat:</span>
              <strong>{new Intl.NumberFormat('vi-VN').format(selected.fare_per_seat)} VND</strong>
            </div>
          </div>

          <form onSubmit={handleConfirm}>
            <label className={styles.label}>
              Number of Seats
              <input 
                className={styles.input}
                type="number" 
                min={1} 
                max={selected.remaining_seats} 
                value={seats} 
                onChange={(e) => setSeats(e.target.value)} 
              />
            </label>

            <div className={styles.totalAmount}>
              <span>Total Amount:</span>
              <strong>{new Intl.NumberFormat('vi-VN').format(selected.fare_per_seat * seats)} VND</strong>
            </div>

            <button className={styles.button} type="submit" disabled={loading}>
              {loading ? "Processing..." : "Confirm Booking"}
            </button>
          </form>
        </>
      )}
    </div>
  );
}