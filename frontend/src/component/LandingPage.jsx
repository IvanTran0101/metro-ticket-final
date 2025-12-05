import styles from "./LandingPage.module.css";

export default function LandingPage({ onNavigate }) {
    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <h1 className={styles.title}>METRO FLOW</h1>

                <div className={styles.buttonGroup}>
                    <button
                        className={`${styles.button} ${styles.purchase}`}
                        onClick={() => onNavigate("login")}
                    >
                        PURCHASE TICKET
                    </button>

                    <button
                        className={`${styles.button} ${styles.checkin}`}
                        onClick={() => onNavigate("checkin")}
                    >
                        CHECK-IN GATE
                    </button>

                    <button
                        className={`${styles.button} ${styles.checkout}`}
                        onClick={() => onNavigate("checkout")}
                    >
                        CHECK-OUT GATE
                    </button>
                </div>
            </div>
        </div>
    );
}
