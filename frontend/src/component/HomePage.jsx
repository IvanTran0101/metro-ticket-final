import styles from "./HomePage.module.css";
import TicketMachine from "./TicketMachine";

export default function HomePage({ me, onLogout, onNavigate, onRefresh }) {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.logo}>🚇 MetroFlow</div>
        <div className={styles.user}>
          <button onClick={() => onNavigate('schedule')} className={styles.navBtn}>📅 View Schedule</button>
          <span>Welcome, {me?.name} ({me?.passenger_type})</span>
          <span className={styles.balance}>Balance: {me?.balance?.toLocaleString()} VND</span>
          <button onClick={onLogout} className={styles.logoutBtn}>Logout</button>
        </div>
      </header>

      <main className={styles.main}>
        <div className={styles.content}>
          <TicketMachine onPurchaseSuccess={onRefresh} />
        </div>
      </main>
    </div>
  );
}
