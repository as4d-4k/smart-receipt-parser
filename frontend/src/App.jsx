import { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('scanner'); 
  const [selectedFile, setSelectedFile] = useState(null)
  const [scanResult, setScanResult] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [history, setHistory] = useState([]) 
  const [viewingScan, setViewingScan] = useState(null) 

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/history')
      const data = await response.json()
      setHistory(data.reverse())
    } catch (error) {
      console.error("Error fetching history:", error)
    }
  }

  const getChartData = () => {
    const data = {};
    history.forEach(scan => {
      const cat = scan.category || "EXPENSE";
      const amount = parseFloat(scan.total) || 0;
      if (data[cat]) data[cat] += amount;
      else data[cat] = amount;
    });
    return Object.keys(data).map(key => ({
      name: key,
      value: parseFloat(data[key].toFixed(2))
    }));
  };
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#ff6b6b'];
  const chartData = getChartData();

  const handleFileChange = (event) => {
    const file = event.target.files[0]
    if (file) {
      setSelectedFile(file)
      setScanResult(null) 
    }
  }

  const handleScan = async () => {
    if (!selectedFile) {
        alert("Please select a file first!")
        return
    }
    setIsLoading(true) 
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      const response = await fetch('http://127.0.0.1:5000/api/scan', {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      if (response.ok) {
        setScanResult(data.data)
        fetchHistory() 
      } else {
        alert("Error scanning receipt: " + data.error)
      }
    } catch (error) {
      console.error("Error:", error)
      alert("Failed to connect to the server.")
    } finally {
      setIsLoading(false) 
    }
  }

  return (
    <div className="app-layout">
      
      {/* --- SIDEBAR --- */}
      <nav className="sidebar">
        <div className="logo">🧾 SmartScan</div>
        <button 
          className={activeTab === 'scanner' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setActiveTab('scanner')}
        >
          📷 Scan Receipt
        </button>
        <button 
          className={activeTab === 'insights' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setActiveTab('insights')}
        >
          📊 Insights & History
        </button>
      </nav>

      {/* --- MAIN CONTENT --- */}
      <main className="main-content">
        
        {/* === TAB 1: SCANNER === */}
        {activeTab === 'scanner' && (
          <div className="scanner-container">
            <header>
              <h1>New Scan</h1>
              <p>Upload a receipt to extract data instantly.</p>
            </header>

            <div className="upload-card">
              <input type="file" id="file-input" onChange={handleFileChange} accept="image/*" />
              <label htmlFor="file-input" className="file-label">
                {selectedFile ? selectedFile.name : "Click to Choose Image"}
              </label>
              
              <button className="scan-btn" onClick={handleScan} disabled={isLoading}>
                {isLoading ? "Processing..." : "Extract Data"}
              </button>
            </div>

            <div className="scan-preview-area">
              {selectedFile && (
                <div className="preview-box">
                  <img src={URL.createObjectURL(selectedFile)} alt="Preview" />
                </div>
              )}

              {scanResult && (
                <div className="result-card fade-in">
                  <div className="result-header">
                    <span className={`category-badge ${scanResult.category}`}>
                      {scanResult.category || "EXPENSE"}
                    </span>
                    <span className="result-date">{scanResult.date}</span>
                  </div>
                  
                  <div className="result-total">
                    <span className="label">Total</span>
                    {/* SHOW CURRENCY HERE */}
                    <span className="amount">
                       {scanResult.currency} {scanResult.total}
                    </span>
                  </div>

                  <div className="items-table-wrapper">
                    <table className="items-table">
                      <tbody>
                        {scanResult.items.map((item, index) => (
                          <tr key={index}>
                            <td className="qty-col">{item.qty || 1}x</td>
                            <td>{item.name}</td>
                            {/* SHOW CURRENCY HERE */}
                            <td className="price-col">
                                {scanResult.currency} {item.price}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* === TAB 2: INSIGHTS === */}
        {activeTab === 'insights' && (
          <div className="insights-container fade-in">
            <header>
              <h1>Spending Insights</h1>
              <p>Analyze your expenses by category.</p>
            </header>

            <div className="chart-card">
              <h3>Category Breakdown</h3>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={80}
                      outerRadius={110}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{backgroundColor: '#222', border: '1px solid #444', borderRadius: '8px'}} itemStyle={{color: '#fff'}} />
                    <Legend verticalAlign="bottom" height={36}/>
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="history-list-section">
              <h3>Recent History</h3>
              <div className="history-grid">
                {history.map((scan, index) => (
                  <div key={index} className="history-card" onClick={() => setViewingScan(scan)}>
                    <div className="card-top">
                      <span className={`category-dot ${scan.category}`}></span>
                      <span className="card-date">{scan.date}</span>
                    </div>
                    {/* SHOW CURRENCY (Handle old scans with no currency) */}
                    <div className="card-total">
                        {scan.currency || ''} {scan.total}
                    </div>
                    <div className="card-items">
                      {scan.items.length} items • {scan.category || "Expense"}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* --- MODAL (Shared) --- */}
      {viewingScan && (
        <div className="modal-overlay" onClick={() => setViewingScan(null)}>
          <div className="modal-content fade-in" onClick={(e) => e.stopPropagation()}>
            <button className="close-btn" onClick={() => setViewingScan(null)}>×</button>
            
            <div className="modal-header">
              <span className={`category-badge ${viewingScan.category}`}>
                 {viewingScan.category || "EXPENSE"}
              </span>
              <h2>Receipt Details</h2>
            </div>

            <div className="modal-info">
              <div className="info-row">
                <span>Date</span>
                <strong>{viewingScan.date}</strong>
              </div>
              <div className="info-row total-row">
                <span>Total</span>
                {/* SHOW CURRENCY HERE */}
                <strong>{viewingScan.currency || ''} {viewingScan.total}</strong>
              </div>
            </div>
            
            <div className="modal-table-container">
              <table className="items-table">
                <thead>
                  <tr>
                    <th>Qty</th>
                    <th>Item</th>
                    <th style={{textAlign: 'right'}}>Price</th>
                  </tr>
                </thead>
                <tbody>
                  {viewingScan.items && viewingScan.items.map((item, index) => (
                    <tr key={index}>
                      <td style={{color: '#888'}}>{item.qty || 1}</td>
                      <td>{item.name}</td>
                      {/* SHOW CURRENCY HERE */}
                      <td style={{textAlign: 'right'}}>
                        {viewingScan.currency || ''} {item.price}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App