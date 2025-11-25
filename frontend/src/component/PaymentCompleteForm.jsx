import { useMemo } from "react";
import styles from "./PaymentCompleteForm.module.css";

export default function PaymentCompleteForm({
  me,
  bookingDetails,
  paymentAmount,
  paymentId,
  onBackToHome,
}) {
  // FIX: The 'me' object contains the snapshot of the user BEFORE payment.
  // So 'originalBalance' is just the current balance in 'me'.
  const originalBalance = useMemo(() => {
    return Number(me?.balance ?? 0);
  }, [me?.balance]);

  // FIX: New Balance is Original minus Payment
  const newBalance = useMemo(() => {
    const current = Number(me?.balance ?? 0);
    const deducted = Number(paymentAmount ?? 0);
    return current - deducted;
  }, [me?.balance, paymentAmount]);

  const balanceFmt = useMemo(() => {
    return newBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }, [newBalance]);

  const originalBalanceFmt = useMemo(() => {
    return originalBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }, [originalBalance]);

  const paymentFmt = useMemo(() => {
    return Number(paymentAmount || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }, [paymentAmount]);

  const seatFareFmt = useMemo(() => {
    return Number(bookingDetails?.seat_fare || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  }, [bookingDetails?.seat_fare]);

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h2 className={styles.title}>✓ Payment Successful</h2>
        <p className={styles.subtitle}>Your booking payment has been completed</p>
      </div>

      {/* Payment Reference */}
      <div className={styles.section}>
        <h3>Payment Reference</h3>
        <div className={styles.infoRow}>
          <span className={styles.label}>Payment ID:</span>
          <span className={styles.value}>{paymentId}</span>
        </div>
        <div className={styles.infoRow}>
          <span className={styles.label}>Completed At:</span>
          <span className={styles.value}>{new Date().toLocaleString()}</span>
        </div>
      </div>

      {/* Payer Information */}
      <div className={styles.section}>
        <h3>Payer Information</h3>
        <div className={styles.infoRow}>
          <span className={styles.label}>Full Name:</span>
          <span className={styles.value}>{me?.full_name || ""}</span>
        </div>
        <div className={styles.infoRow}>
          <span className={styles.label}>Email:</span>
          <span className={styles.value}>{me?.email || ""}</span>
        </div>
        <div className={styles.infoRow}>
          <span className={styles.label}>Phone:</span>
          <span className={styles.value}>{me?.phone_number || ""}</span>
        </div>
      </div>

      {/* Booking Information */}
      {bookingDetails && (
        <div className={styles.section}>
          <h3>Booking Information</h3>
          <div className={styles.infoRow}>
            <span className={styles.label}>Booking Code:</span>
            <span className={styles.value}>{bookingDetails.booking_code}</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.label}>Seats Reserved:</span>
            <span className={styles.value}>{bookingDetails.seats}</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.label}>Seat Fare:</span>
            <span className={styles.value}>{seatFareFmt} VND</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.label}>Total Amount:</span>
            <span className={styles.value}>{Number(bookingDetails.total_amount || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })} VND</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.label}>Booking Date:</span>
            <span className={styles.value}>{bookingDetails.created_at ? new Date(bookingDetails.created_at).toLocaleString() : ""}</span>
          </div>
        </div>
      )}

      {/* Balance Summary */}
      <div className={styles.balanceSection}>
        <h3>Account Balance Summary</h3>
        <div className={styles.balanceRow}>
          <span>Previous Balance:</span>
          <span className={styles.balanceValue}>{originalBalanceFmt} VND</span>
        </div>
        <div className={styles.balanceRow} style={{ borderTop: "1px solid #ddd", paddingTop: "8px", marginTop: "8px" }}>
          <span className={styles.deduction}>Amount Deducted:</span>
          <span className={styles.deductionValue}>- {paymentFmt} VND</span>
        </div>
        <div className={styles.balanceRow} style={{ borderTop: "2px solid #333", paddingTop: "8px", marginTop: "8px", fontWeight: "bold" }}>
          <span>Current Balance:</span>
          <span className={styles.currentBalance}>{balanceFmt} VND</span>
        </div>
      </div>

      {/* Action Button */}
      <div className={styles.buttonGroup}>
        <button className={styles.button} type="button" onClick={onBackToHome}>
          Back to Home
        </button>
      </div>
    </div>
  );
}