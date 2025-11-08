import { useState, useEffect } from 'react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import './App.css'

const API_URL = 'http://localhost:8000'

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [role, setRole] = useState(localStorage.getItem('role'))
  const [view, setView] = useState('chat')

  // Auth states
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [selectedRole, setSelectedRole] = useState('investor')

  // Chat states
  const [stockSymbol, setStockSymbol] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  // Reports states
  const [reports, setReports] = useState([])

  // Portfolio states
  const [portfolio, setPortfolio] = useState([])
  const [portfolioSummary, setPortfolioSummary] = useState(null)

  // Analyst states
  const [investors, setInvestors] = useState([])
  const [selectedInvestor, setSelectedInvestor] = useState(null)
  const [investorPortfolio, setInvestorPortfolio] = useState([])
  const [investorReports, setInvestorReports] = useState([])

  const handleAuth = async (e) => {
    e.preventDefault()
    try {
      if (isLogin) {
        const res = await axios.post(`${API_URL}/login`, { username, password })
        setToken(res.data.access_token)
        setRole(res.data.role)
        localStorage.setItem('token', res.data.access_token)
        localStorage.setItem('role', res.data.role)

        if (res.data.role === 'analyst') {
          setView('investors')
        } else {
          setView('portfolio')
        }
      } else {
        await axios.post(`${API_URL}/register`, {
          username,
          password,
          role: selectedRole
        })
        alert('Registration successful! Please login.')
        setIsLogin(true)
        setUsername('')
        setPassword('')
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Authentication failed')
    }
  }

  const handleAnalyze = async (e) => {
    e.preventDefault()
    if (!stockSymbol.trim()) return

    setLoading(true)
    try {
      const res = await axios.post(
        `${API_URL}/chat?token=${token}`,
        {
          stock_symbol: stockSymbol.toUpperCase(),
          question: 'Analyze this stock and give trading recommendations'
        }
      )

      setMessages([...messages, {
        type: 'analysis',
        data: res.data
      }])
      setStockSymbol('')
    } catch (err) {
      alert(err.response?.data?.detail || 'Analysis failed')
    }
    setLoading(false)
  }

  const handleAddToPortfolio = async (stockData, quantity) => {
    try {
      await axios.post(
        `${API_URL}/portfolio/add?token=${token}`,
        null,
        {
          params: {
            stock_symbol: stockData.symbol,
            quantity: parseFloat(quantity),
            purchase_price: stockData.price
          }
        }
      )
      alert(`✅ Bought ${quantity} shares of ${stockData.symbol} at $${stockData.price}`)
      if (view === 'portfolio') {
        loadPortfolio()
      }
    } catch (err) {
      alert('❌ Failed: ' + (err.response?.data?.detail || 'Error'))
    }
  }

  const handleSellFromPortfolio = async (stockData, quantity) => {
    try {
      await axios.post(
        `${API_URL}/portfolio/add?token=${token}`,
        null,
        {
          params: {
            stock_symbol: stockData.symbol,
            quantity: -parseFloat(quantity),
            purchase_price: stockData.price
          }
        }
      )
      alert(`✅ Sold ${quantity} shares of ${stockData.symbol} at $${stockData.price}`)
      if (view === 'portfolio') {
        loadPortfolio()
      }
    } catch (err) {
      alert('❌ Failed: ' + (err.response?.data?.detail || 'Error'))
    }
  }

  const handleRemoveFromPortfolio = async (stockSymbol) => {
    if (window.confirm(`Remove all ${stockSymbol} positions from portfolio?`)) {
      try {
        await axios.delete(`${API_URL}/portfolio/remove?stock_symbol=${stockSymbol}&token=${token}`)
        alert(`✅ Removed ${stockSymbol} from portfolio`)
        loadPortfolio()
      } catch (err) {
        alert('❌ Failed to remove: ' + (err.response?.data?.detail || 'Error'))
      }
    }
  }

  const loadReports = async () => {
    try {
      const res = await axios.get(`${API_URL}/reports?token=${token}`)
      setReports(res.data.reports)
    } catch (err) {
      alert('Failed to load reports')
    }
  }

  const loadPortfolio = async (userId = null) => {
    try {
      const endpoint = userId
        ? `${API_URL}/portfolio/consolidated/${userId}?token=${token}`
        : `${API_URL}/portfolio/consolidated/1?token=${token}`

      const res = await axios.get(endpoint)
      if (userId) {
        setInvestorPortfolio(res.data.portfolio)
      } else {
        setPortfolio(res.data.portfolio)
        setPortfolioSummary(res.data.summary)
      }
    } catch (err) {
      console.error('Failed to load portfolio', err)
    }
  }

  const loadInvestors = async () => {
    try {
      const res = await axios.get(`${API_URL}/investors?token=${token}`)
      setInvestors(res.data.investors)
    } catch (err) {
      alert('Failed to load investors')
    }
  }

  const selectInvestor = async (investor) => {
    setSelectedInvestor(investor)
    try {
      const portfolioRes = await axios.get(`${API_URL}/portfolio/consolidated/${investor.id}?token=${token}`)
      setInvestorPortfolio(portfolioRes.data.portfolio)

      const reportsRes = await axios.get(`${API_URL}/reports/${investor.id}?token=${token}`)
      setInvestorReports(reportsRes.data.reports)
    } catch (err) {
      alert('Failed to load investor data')
    }
  }

  const logout = () => {
    setToken(null)
    setRole(null)
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    setMessages([])
    setView('chat')

    // Clear form fields
    setUsername('')
    setPassword('')
    setSelectedRole('investor')
    setIsLogin(true)
  }

  useEffect(() => {
    if (token && view === 'reports') {
      loadReports()
    } else if (token && view === 'portfolio' && role === 'investor') {
      loadPortfolio()
    } else if (token && view === 'investors' && role === 'analyst') {
      loadInvestors()
    }
  }, [token, view, role])

  // Not logged in
  if (!token) {
    return (
      <div className="auth-container">
        <div className="auth-box">
          <h1>📈 Stock Analyst AI</h1>
          <h2>{isLogin ? 'Login' : 'Register'}</h2>

          <form onSubmit={handleAuth}>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            {!isLogin && (
              <select value={selectedRole} onChange={(e) => setSelectedRole(e.target.value)}>
                <option value="investor">Investor</option>
                <option value="analyst">Analyst</option>
              </select>
            )}

            <button type="submit">{isLogin ? 'Login' : 'Register'}</button>
          </form>

          <p onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? 'Need an account? Register' : 'Have an account? Login'}
          </p>
        </div>
      </div>
    )
  }

  // Logged in
  return (
    <div className="container">
      <nav className="navbar">
        <h1>📈 Stock Analyst AI</h1>
        <div>
          <span className="role-badge">{role}</span>

          {role === 'analyst' ? (
            <>
              <button onClick={() => setView('investors')} className={view === 'investors' ? 'active' : ''}>
                Investors
              </button>
              <button onClick={() => setView('chat')} className={view === 'chat' ? 'active' : ''}>
                Analyze
              </button>
            </>
          ) : (
            <>
              <button onClick={() => setView('portfolio')} className={view === 'portfolio' ? 'active' : ''}>
                Portfolio
              </button>
              <button onClick={() => setView('chat')} className={view === 'chat' ? 'active' : ''}>
                Chat
              </button>
              <button onClick={() => setView('reports')} className={view === 'reports' ? 'active' : ''}>
                Reports
              </button>
            </>
          )}

          <button onClick={logout}>Logout</button>
        </div>
      </nav>

      {/* ANALYST: Investors List */}
      {role === 'analyst' && view === 'investors' && !selectedInvestor && (
        <div className="investors-container">
          <h2>My Investors</h2>
          <div className="investors-list">
            {investors.length === 0 ? (
              <p>No investors yet.</p>
            ) : (
              investors.map((investor) => (
                <div key={investor.id} className="investor-card" onClick={() => selectInvestor(investor)}>
                  <h3>👤 {investor.username}</h3>
                  <p>Click to view portfolio and reports</p>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* ANALYST: Selected Investor Detail */}
      {role === 'analyst' && view === 'investors' && selectedInvestor && (
        <div className="investor-detail">
          <button onClick={() => setSelectedInvestor(null)} className="back-btn">← Back to Investors</button>

          <h2>👤 {selectedInvestor.username}'s Portfolio</h2>

          <div className="portfolio-section">
            <h3>Holdings</h3>
            {investorPortfolio.length === 0 ? (
              <p>No holdings yet.</p>
            ) : (
              <table className="portfolio-table">
                <thead>
                  <tr>
                    <th>Stock</th>
                    <th>Quantity</th>
                    <th>Avg Price</th>
                    <th>Current</th>
                    <th>Value</th>
                    <th>P/L</th>
                  </tr>
                </thead>
                <tbody>
                  {investorPortfolio.map((holding, idx) => (
                    <tr key={idx}>
                      <td><strong>{holding.stock}</strong></td>
                      <td>{holding.quantity}</td>
                      <td>${holding.purchase_price}</td>
                      <td>${holding.current_price}</td>
                      <td>${holding.total_value}</td>
                      <td className={holding.profit_loss >= 0 ? 'positive' : 'negative'}>
                        ${holding.profit_loss} ({holding.profit_loss_pct}%)
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="reports-section">
            <h3>Recent Analyses</h3>
            {investorReports.length === 0 ? (
              <p>No reports yet.</p>
            ) : (
              <div className="reports-list">
                {investorReports.map((report, idx) => (
                  <div key={idx} className="report-card">
                    <h3>{report.stock}</h3>
                    <p className="timestamp">{new Date(report.timestamp).toLocaleString()}</p>
                    <p>{report.analysis}</p>
                    <span className={`rec-badge ${report.recommendation.toLowerCase().replace(' ', '-')}`}>
                      {report.recommendation}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* INVESTOR: Portfolio */}
      {role === 'investor' && view === 'portfolio' && (
        <div className="portfolio-container">
          <h2>My Portfolio</h2>

          {portfolioSummary && portfolio.length > 0 && (
            <div className="portfolio-summary">
              <div className="summary-card">
                <h3>Total Value</h3>
                <p className="big-number">${portfolioSummary.total_value.toFixed(2)}</p>
              </div>
              <div className="summary-card">
                <h3>Total P/L</h3>
                <p className={`big-number ${portfolioSummary.total_profit_loss >= 0 ? 'positive' : 'negative'}`}>
                  ${portfolioSummary.total_profit_loss.toFixed(2)}
                </p>
              </div>
              <div className="summary-card">
                <h3>Positions</h3>
                <p className="big-number">{portfolioSummary.total_positions}</p>
              </div>
            </div>
          )}

          {portfolio.length === 0 ? (
            <div className="welcome">
              <p>Your portfolio is empty. Start analyzing stocks to build your portfolio!</p>
            </div>
          ) : (
            <table className="portfolio-table">
              <thead>
                <tr>
                  <th>Stock</th>
                  <th>Quantity</th>
                  <th>Avg Price</th>
                  <th>Current Price</th>
                  <th>Total Value</th>
                  <th>Profit/Loss</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.map((holding, idx) => (
                  <tr key={idx}>
                    <td><strong>{holding.stock}</strong></td>
                    <td>{holding.quantity}</td>
                    <td>${holding.purchase_price}</td>
                    <td>${holding.current_price}</td>
                    <td>${holding.total_value}</td>
                    <td className={holding.profit_loss >= 0 ? 'positive' : 'negative'}>
                      ${holding.profit_loss} ({holding.profit_loss_pct}%)
                    </td>
                    <td>
                      <button
                        className="remove-btn"
                        onClick={() => handleRemoveFromPortfolio(holding.stock)}
                      >
                        🗑️ Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* CHAT VIEW */}
      {view === 'chat' && (
        <div className="chat-container">
          <div className="messages">
            {messages.length === 0 ? (
              <div className="welcome">
                <h2>Welcome, {role}!</h2>
                <p>Enter a stock symbol (e.g., AAPL, TSLA, GOOGL) to get AI-powered analysis</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className="message">
                  <div className="stock-info">
                    <h3>{msg.data.stock_data.symbol} - {msg.data.stock_data.name}</h3>
                    <div className="price">
                      <span className="current">${msg.data.stock_data.price}</span>
                      <span className={msg.data.stock_data.change >= 0 ? 'positive' : 'negative'}>
                        {msg.data.stock_data.change >= 0 ? '▲' : '▼'}
                        {msg.data.stock_data.percent_change}%
                      </span>
                    </div>
                  </div>

                  <div className="analysis">
                    <h4>AI Analysis</h4>
                    <p>{msg.data.analysis.analysis || 'Analysis in progress...'}</p>

                    <div className="recommendation">
                      <span className={`rec-badge ${msg.data.analysis.recommendation.toLowerCase().replace(' ', '-')}`}>
                        {msg.data.analysis.recommendation}
                      </span>
                      <span className="allocation">
                        Portfolio Allocation: {msg.data.analysis.portfolio_percent}%
                      </span>
                    </div>

                    {msg.data.analysis.reasoning && (
                      <p className="reasoning"><strong>Reasoning:</strong> {msg.data.analysis.reasoning}</p>
                    )}

                    {/* Portfolio Actions for investors */}
                    {role === 'investor' && (
                      <div className="portfolio-actions">
                        <h4>Portfolio Actions</h4>
                        <div className="action-form">
                          <input
                            type="number"
                            placeholder="Quantity"
                            min="0.01"
                            step="0.01"
                            id={`qty-${idx}`}
                            defaultValue="1"
                            className="qty-input"
                            onChange={(e) => {
                              const total = parseFloat(e.target.value || 0) * msg.data.stock_data.price
                              document.getElementById(`total-${idx}`).textContent = total.toFixed(2)
                            }}
                          />
                          <button
                            className="action-btn buy-btn"
                            onClick={() => {
                              const qty = document.getElementById(`qty-${idx}`).value
                              if (qty && parseFloat(qty) > 0) {
                                handleAddToPortfolio(msg.data.stock_data, qty)
                              } else {
                                alert('Please enter a valid quantity')
                              }
                            }}
                          >
                            📈 Buy
                          </button>
                          <button
                            className="action-btn sell-btn"
                            onClick={() => {
                              const qty = document.getElementById(`qty-${idx}`).value
                              if (qty && parseFloat(qty) > 0) {
                                handleSellFromPortfolio(msg.data.stock_data, qty)
                              } else {
                                alert('Please enter a valid quantity')
                              }
                            }}
                          >
                            📉 Sell
                          </button>
                        </div>
                        <p className="action-hint">
                          Current Price: ${msg.data.stock_data.price} |
                          Total: $<span id={`total-${idx}`}>{msg.data.stock_data.price.toFixed(2)}</span>
                        </p>
                      </div>
                    )}
                  </div>

                  {msg.data.chart_data && (
                    <div className="chart">
                      <h4>30-Day Price Trend</h4>
                      <LineChart width={600} height={200} data={
                        msg.data.chart_data.labels.map((label, i) => ({
                          day: label,
                          price: msg.data.chart_data.prices[i]
                        }))
                      }>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="day" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="price" stroke="#4CAF50" strokeWidth={2} />
                      </LineChart>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          <form className="input-form" onSubmit={handleAnalyze}>
            <input
              type="text"
              placeholder="Enter stock symbol (e.g., AAPL, TSLA)..."
              value={stockSymbol}
              onChange={(e) => setStockSymbol(e.target.value)}
              disabled={loading}
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>
          </form>
        </div>
      )}

      {/* REPORTS VIEW */}
      {role === 'investor' && view === 'reports' && (
        <div className="reports-container">
          <h2>My Analysis Reports</h2>
          {reports.length === 0 ? (
            <p>No reports yet. Start analyzing stocks!</p>
          ) : (
            <div className="reports-list">
              {reports.map((report, idx) => (
                <div key={idx} className="report-card">
                  <h3>{report.stock}</h3>
                  <p className="timestamp">{new Date(report.timestamp).toLocaleString()}</p>
                  <p>{report.analysis}</p>
                  <span className={`rec-badge ${report.recommendation.toLowerCase().replace(' ', '-')}`}>
                    {report.recommendation}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default App