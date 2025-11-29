import { useState, useEffect } from 'react'
import './App.css'
import LoginForm from './component/LoginForm.jsx'
import HomePage from './component/HomePage.jsx'
import SchedulerForm from './component/SchedulerForm.jsx'
import PaymentForm from './component/PaymentForm.jsx'
import PaymentHistoryForm from './component/PaymentHistoryForm.jsx'

function App() {
  const [loggedIn, setLoggedIn] = useState(false)
  const [view, setView] = useState("home") // 'home' | 'scheduler' | 'payment' | 'history'
  const [bookingData, setBookingData] = useState(null)
  const [viewHistory, setViewHistory] = useState(["home"])

  // Handle browser back button
  useEffect(() => {
    const handlePopState = () => {
      if (viewHistory.length > 1) {
        const newHistory = viewHistory.slice(0, -1)
        setViewHistory(newHistory)
        setView(newHistory[newHistory.length - 1])
        setBookingData(null)
      }
    }

    window.addEventListener("popstate", handlePopState)
    return () => window.removeEventListener("popstate", handlePopState)
  }, [viewHistory])

  const navigateTo = (newView: string) => {
    setView(newView)
    setViewHistory([...viewHistory, newView])
    window.history.pushState(null, "", window.location.href)
  }

  if (!loggedIn) {
    return (
      <div className="app-root">
        <LoginForm onLoggedIn={() => setLoggedIn(true)} />
      </div>
    )
  }

  return (
    <div className="app-root">
      {view === "home" && (
        <HomePage
          onLoggedOut={() => { setLoggedIn(false); setView("home"); setBookingData(null); setViewHistory(["home"]) }}
          onStartBooking={() => { navigateTo("scheduler"); setBookingData(null); }}
          onViewPaymentHistory={() => { navigateTo("history"); }}
        />
      )}
      {view === "scheduler" && (
        <SchedulerForm 
          onBookingConfirmed={(b: any) => { setBookingData(b); navigateTo("payment"); }} 
        />
      )}
      {view === "payment" && (
        <PaymentForm
          booking={bookingData}
          onLoggedOut={() => { setLoggedIn(false); setView("home"); setBookingData(null); setViewHistory(["home"]) }}
          onBackToScheduler={() => { navigateTo("home"); setBookingData(null); }}
        />
      )}
      {view === "history" && (
        <PaymentHistoryForm />
      )}
    </div>
  )
}

export default App
