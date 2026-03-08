import { useState, useEffect } from 'react'
import './App.css'

// Use relative path when served behind nginx proxy; full URL for standalone dev
const API_URL = import.meta.env.VITE_GATEWAY_URL || ''

function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAnalytics = async () => {
    try {
      const res = await fetch(API_URL ? `${API_URL}/api/analytics` : '/api/analytics')
      if (!res.ok) throw new Error('Failed to fetch')
      const json = await res.json()
      setData(json)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalytics()
    const interval = setInterval(fetchAnalytics, 5000)
    return () => clearInterval(interval)
  }, [])

  if (loading && !data) {
    return (
      <div className="app">
        <div className="loading">Connecting to gateway...</div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="app">
        <div className="error">
          <h2>Cannot connect to gateway</h2>
          <p>{error}</p>
          <p className="hint">Ensure the gateway is running (port 8000) and CORS is enabled</p>
          <button onClick={fetchAnalytics}>Retry</button>
        </div>
      </div>
    )
  }

  const { total_requests = 0, by_status = {}, by_path = {}, recent_logs = [] } = data || {}

  return (
    <div className="app">
      <header>
        <h1>API Gateway Analytics</h1>
        <span className="badge">Live</span>
      </header>

      <section className="stats">
        <div className="stat-card primary">
          <span className="stat-value">{total_requests.toLocaleString()}</span>
          <span className="stat-label">Total Requests</span>
        </div>
        {Object.entries(by_status).map(([code, count]) => (
          <div key={code} className={`stat-card ${code.startsWith('2') ? 'success' : code.startsWith('4') ? 'warn' : 'error'}`}>
            <span className="stat-value">{count.toLocaleString()}</span>
            <span className="stat-label">{code} responses</span>
          </div>
        ))}
      </section>

      <section className="paths">
        <h2>Top Paths</h2>
        <div className="path-list">
          {Object.entries(by_path)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .map(([path, count]) => (
              <div key={path} className="path-row">
                <code>{path}</code>
                <span>{count}</span>
              </div>
            ))}
          {Object.keys(by_path).length === 0 && <p className="empty">No path data yet</p>}
        </div>
      </section>

      <section className="logs">
        <h2>Recent Requests</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Method</th>
                <th>Path</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Client</th>
              </tr>
            </thead>
            <tbody>
              {recent_logs.map((log, i) => (
                <tr key={i}>
                  <td>{new Date(log.timestamp).toLocaleTimeString()}</td>
                  <td><span className={`method ${log.method}`}>{log.method}</span></td>
                  <td><code>{log.path}</code></td>
                  <td><span className={`status s${String(log.status_code)[0]}`}>{log.status_code}</span></td>
                  <td>{log.duration_ms}ms</td>
                  <td>{log.client_ip}</td>
                </tr>
              ))}
              {recent_logs.length === 0 && (
                <tr><td colSpan={6}>No requests logged yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

export default App
