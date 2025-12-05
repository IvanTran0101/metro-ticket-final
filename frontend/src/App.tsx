import { useState, useEffect } from 'react'
import './App.css'
import LoginForm from './component/LoginForm.jsx'
import LandingPage from './component/LandingPage.jsx'
import GateCheckIn from './component/GateCheckIn.jsx'
import GateCheckOut from './component/GateCheckOut.jsx'
import SchedulerForm from './component/SchedulerForm.jsx'
import { getAccountMe, type AccountMeResponse } from './api/account'
import { getToken, logout } from './api/auth'

function App() {
  // Views: 'landing', 'login', 'home', 'checkin', 'checkout', 'schedule'
  const [currentView, setCurrentView] = useState('landing')
  const [me, setMe] = useState<AccountMeResponse | null>(null)

  useEffect(() => {
    // Check if token exists
    const token = getToken()
    if (token) {
      fetchMe()
    }
  }, [])

  async function fetchMe() {
    try {
      const res = await getAccountMe()
      setMe(res)
    } catch (e) {
      console.error("Failed to fetch user info", e)
      logout()
      setMe(null)
    }
  }

  function handleLogin() {
    fetchMe().then(() => setCurrentView('schedule'))
  }

  function handleLogout() {
    setMe(null)
    logout()
    setCurrentView('landing')
  }

  function handleNavigate(view: string) {
    if (view === 'login') {
      if (me) {
        setCurrentView('schedule')
      } else {
        setCurrentView('login')
      }
    } else {
      setCurrentView(view)
    }
  }

  // Render Logic
  if (currentView === 'landing') {
    return <LandingPage onNavigate={handleNavigate} />
  }

  if (currentView === 'checkin') {
    return (
      <div className="app-root">
        <button className="back-btn" onClick={() => setCurrentView('landing')}>← Back</button>
        <GateCheckIn />
      </div>
    )
  }

  if (currentView === 'checkout') {
    return (
      <div className="app-root">
        <button className="back-btn" onClick={() => setCurrentView('landing')}>← Back</button>
        <GateCheckOut />
      </div>
    )
  }

  if (currentView === 'login') {
    return (
      <div className="app-root">
        <button className="back-btn" onClick={() => setCurrentView('landing')}>← Back</button>
        <LoginForm onLoggedIn={handleLogin} />
      </div>
    )
  }

  // Authenticated Views
  if (me) {
    // Default to SchedulerForm (acting as Home)
    return (
      <div className="app-root">
        <SchedulerForm me={me} onLogout={handleLogout} />
      </div>
    )
  }

  // Fallback if not logged in
  return <LandingPage onNavigate={handleNavigate} />
}

export default App
