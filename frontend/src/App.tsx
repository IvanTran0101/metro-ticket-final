import { useState, useEffect } from 'react'
import './App.css'
import LoginForm from './component/LoginForm.jsx'
import HomePage from './component/HomePage.jsx'
import { client } from './api/client'

function App() {
  const [loggedIn, setLoggedIn] = useState(false)
  const [me, setMe] = useState(null)

  useEffect(() => {
    // Check if token exists
    const token = localStorage.getItem("access_token")
    if (token) {
      setLoggedIn(true)
      fetchMe()
    }
  }, [])

  async function fetchMe() {
    try {
      const res = await client.get("/account/me")
      setMe(res)
    } catch (e) {
      console.error("Failed to fetch user info", e)
      // If token invalid, logout
      setLoggedIn(false)
      localStorage.removeItem("access_token")
    }
  }

  function handleLogin() {
    setLoggedIn(true)
    fetchMe()
  }

  function handleLogout() {
    setLoggedIn(false)
    setMe(null)
    localStorage.removeItem("access_token")
  }

  if (!loggedIn) {
    return (
      <div className="app-root">
        <LoginForm onLoggedIn={handleLogin} />
      </div>
    )
  }

  return (
    <div className="app-root">
      <HomePage me={me} onLogout={handleLogout} />
    </div>
  )
}

export default App
