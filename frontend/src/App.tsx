import { useState } from 'react'
import './App.css'
import LoginForm from './component/LoginForm.jsx'
import SchedulerForm from './component/SchedulerForm.jsx'
import PaymentForm from './component/PaymentForm.jsx'

function App() {
  const [loggedIn, setLoggedIn] = useState(false)
  const [view, setView] = useState("scheduler") // 'scheduler' | 'payment'
  const [bookingData, setBookingData] = useState(null)

  if (!loggedIn) {
    return (
      <div className="app-root">
        <LoginForm onLoggedIn={() => setLoggedIn(true)} />
      </div>
    )
  }

  return (
    <div className="app-root">
      {view === "scheduler" && (
        <SchedulerForm onBookingConfirmed={(b: any) => { setBookingData(b); setView("payment"); }} />
      )}
      {view === "payment" && (
        <PaymentForm
          booking={bookingData}
          onLoggedOut={() => { setLoggedIn(false); setView("scheduler"); setBookingData(null); }}
          onBackToScheduler={() => { setView("scheduler"); setBookingData(null); }}
        />
      )}
    </div>
  )
}

export default App
