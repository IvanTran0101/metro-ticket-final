import { useState } from "react";
import styles from "./HomePage.module.css";
import TicketMachine from "./TicketMachine";
import GateCheckIn from "./GateCheckIn";
import GateCheckOut from "./GateCheckOut";

export default function HomePage({ me, onLogout }) {
  const [activeTab, setActiveTab] = useState("machine");

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.logo}>🚇 MetroFlow</div>
        <div className={styles.user}>
          <span>Welcome, {me?.name} ({me?.passenger_type})</span>
          <span className={styles.balance}>Balance: {me?.balance?.toLocaleString()} VND</span>
          <button onClick={onLogout} className={styles.logoutBtn}>Logout</button>
        </div>
      </header>

      <main className={styles.main}>
        <div className={styles.tabs}>
          <button
            className={`${styles.tab} ${activeTab === "machine" ? styles.active : ""}`}
            onClick={() => setActiveTab("machine")}
          >
            1. Ticket Machine
          </button>
          <button
            className={`${styles.tab} ${activeTab === "checkin" ? styles.active : ""}`}
            onClick={() => setActiveTab("checkin")}
          >
            2. Check-in Gate
          </button>
          <button
            className={`${styles.tab} ${activeTab === "checkout" ? styles.active : ""}`}
            onClick={() => setActiveTab("checkout")}
          >
            3. Check-out Gate
          </button>
        </div>

        <div className={styles.content}>
          {activeTab === "machine" && <TicketMachine />}
          {activeTab === "checkin" && <GateCheckIn />}
          {activeTab === "checkout" && <GateCheckOut />}
        </div>
      </main>
    </div>
  );
}
