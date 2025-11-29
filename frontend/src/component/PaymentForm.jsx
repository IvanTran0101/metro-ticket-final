import { useEffect, useMemo, useRef, useState } from "react";
import { getAccountMe } from "../api/account";
import { initPayment } from "../api/payment";
import { getBookingDetails } from "../api/booking";
import { logout } from "../api/auth";
import styles from "./PaymentForm.module.css";
import OTPForm from "./OTPForm";
import PaymentCompleteForm from "./PaymentCompleteForm";

const OTP_TTL_MS = Number((import.meta && import.meta.env && import.meta.env.VITE_OTP_TTL_SEC) ?? 300) * 1000;

export default function PaymentForm({ onLoggedOut, booking = null, onBackToScheduler = null }) {
  const [me, setMe] = useState(null);
  const [userId, setUserId] = useState(booking ? (booking.user_id || "") : "");
  const lookupTimer = useRef(null);
  const [totalBookingAmount, setBookingAmount] = useState(booking ? String(booking.total_amount ?? "") : "");
  const [bookingId, setBookingId] = useState(booking ? booking.booking_id : "");
  const [agree, setAgree] = useState(false);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [otpContext, setOtpContext] = useState(null);
  const [bookingDetails, setBookingDetails] = useState(null);
  const [confirmed, setConfirmed] = useState(false);
  const [paymentComplete, setPaymentComplete] = useState(false);
  const [completedPaymentId, setCompletedPaymentId] = useState(null);
  const [previousBalance, setPreviousBalance] = useState(0);
  const [pin, setPin] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const data = await getAccountMe();
        setMe(data);
      } catch (e) {
        setMsg("Failed to load profile. Please re-login.");
      }
    })();
  }, []);

  useEffect(() => {
    if (!booking) return;

    setBookingDetails(booking);
    setBookingId(booking.booking_id || "");
    setBookingAmount(String(booking.total_amount ?? ""));
    setUserId(booking.user_id || "");

    (async () => {
      try {
        const d = await getBookingDetails(booking.booking_id);
        setBookingDetails(d);
      } catch (e) {
        console.error("Failed to refresh booking details in background");
      }
    })();
  }, [booking, me]);

  async function handleLookup() {
    if (booking) return;
    const user_id = (userId || "").trim();
    if (!user_id) return;
    setLoading(true);
    setMsg("");
    try {
      //Dummy
    } catch (e) {
      setBookingId("");
      setBookingAmount("");
    } finally {
      setLoading(false);
    }
  }

  async function handleGetOtp(e) {
    e.preventDefault();
    setMsg("");

    const balance = Number(me?.balance ?? 0);
    const total = Number(totalBookingAmount || 0);

    if (Number.isNaN(total) || total <= 0) return setMsg("Invalid payment amount");
    if (balance < total) {
      setMsg("Insufficient balance. Please top up to confirm payment.");
      return;
    }

    if (!agree) return setMsg("Please accept the terms.");
    const trimmedUserId = userId.trim();

    setOtpContext(null);
    setLoading(true);
    setMsg("");

    try {
      const payload = booking
        ? {
          booking_id: booking.booking_id,
          amount: Number(booking.total_amount ?? totalBookingAmount),
          user_id: me?.user_id || trimmedUserId,
          pin: pin,
        }
        : {
          booking_id: bookingId,
          amount: Number(totalBookingAmount),
          user_id: trimmedUserId,
          pin: pin,
        };

      const res = await initPayment(payload);
      const expiresAt = Date.now() + OTP_TTL_MS;
      setOtpContext({ paymentId: res.payment_id, expiresAt });
      setMsg(`OTP sent for payment ${res.payment_id}. Enter it below within ${Math.floor(OTP_TTL_MS / 60000)} minutes.`);
    } catch (e) {
      setMsg(e?.message || "Failed to start payment");
    } finally {
      setLoading(false);
    }
  }

  function handleOtpVerified(pid) {
    setOtpContext(null);
    setCompletedPaymentId(pid);
    setPreviousBalance(Number(me?.balance ?? 0) + Number(totalBookingAmount || 0));
    setPaymentComplete(true);
    setMsg(`Payment completed successfully!`);
  }

  function handleOtpExpired(pid) {
    setOtpContext(null);
    setMsg(`OTP has expired. Request a new OTP to continue.`);
  }

  const balanceFmt = useMemo(() => {
    const v = Number(me?.balance ?? 0);
    return v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }, [me]);

  useEffect(() => {
    if (lookupTimer.current) clearTimeout(lookupTimer.current);
    if (!userId) return;
    lookupTimer.current = setTimeout(() => handleLookup(), 5000);
    return () => {
      if (lookupTimer.current) clearTimeout(lookupTimer.current);
    };
  }, [userId]);

  const isBalanceLow = Number(me?.balance ?? 0) < Number(totalBookingAmount || 0);

  return (
    <>
      {paymentComplete ? (
        <PaymentCompleteForm
          me={me}
          bookingDetails={bookingDetails}
          paymentAmount={totalBookingAmount}
          paymentId={completedPaymentId}
          previousBalance={previousBalance}
          onBackToHome={() => {
            setPaymentComplete(false);
            setCompletedPaymentId(null);
            onBackToScheduler?.();
          }}
        />
      ) : (
        <form className={styles.card} onSubmit={handleGetOtp}>
          <h2 className={styles.title}>Booking Payment</h2>

          {msg && (
            <div
              className={styles.info}
              style={
                msg.startsWith("OTP verified!")
                  ? { color: "#0f5132" }
                  : undefined
              }
            >
              {msg}
            </div>
          )}

          <h3>1. Payer Information</h3>

          <label className={styles.label}>
            Full Name
            <input className={styles.input} value={me?.name || ""} disabled />
          </label>

          <label className={styles.label}>
            Phone Number
            <input className={styles.input} value={me?.phone_number || ""} disabled />
          </label>

          <label className={styles.label}>
            Email
            <input className={styles.input} value={me?.email || ""} disabled />
          </label>

          <h3>{"2. Booking Information"}</h3>

          <label className={styles.label}>
            Total Amount (VND)
            <input className={styles.input} value={totalBookingAmount} disabled />
          </label>

          {bookingDetails && (
            <>
              <label className={styles.label}>
                Booking Code
                <input
                  className={styles.input}
                  value={bookingDetails.booking_code || ""}
                  disabled
                />
              </label>

              <div style={{ display: 'flex', gap: '10px' }}>
                <label className={styles.label} style={{ flex: 1 }}>
                  Seats
                  <input
                    className={styles.input}
                    value={bookingDetails.seats || 0}
                    disabled
                  />
                </label>

                <label className={styles.label} style={{ flex: 1 }}>
                  Seat Fare (VND)
                  <input
                    className={styles.input}
                    value={new Intl.NumberFormat('vi-VN').format(bookingDetails.seat_fare || 0)}
                    disabled
                  />
                </label>
              </div>

              <label className={styles.label}>
                Created At
                <input
                  className={styles.input}
                  value={bookingDetails.created_at ? new Date(bookingDetails.created_at).toLocaleString() : ''}
                  disabled
                />
              </label>
            </>
          )}

          <div className={styles.balance}>
            <strong>Available Balance:</strong>{" "}
            <span>{balanceFmt} VND</span>
          </div>

          <label className={styles.label}>
            PIN Code
            <input
              className={styles.input}
              type="password"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              placeholder="Enter your 6-digit PIN"
              maxLength={6}
            />
          </label>

          <label className={styles.checkbox}>
            <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
            I agree to the terms and conditions.
          </label>

          <div className={styles.buttonGroup}>
              <button 
                className={`${styles.button} ${isBalanceLow ? styles.faded : ''}`} 
                type="submit" 
                disabled={loading}
              >
                {loading ? "Processing..." : "Confirm & Get OTP"}
              </button>
          </div>

          {otpContext && (
            <OTPForm
              key={otpContext.bookingId}
              bookingId={bookingId}
              expiresAt={otpContext.expiresAt}
              onVerified={handleOtpVerified}
              onExpired={handleOtpExpired}
            />
          )}
        </form>
      )}
    </>
  );
}