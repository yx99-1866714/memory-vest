import React, { useState } from 'react';
import { UploadCloud, TrendingUp, DollarSign, Briefcase, Edit2, Trash2, Check, X, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import './Dashboard.css';

export default function Dashboard({ userId }) {
  const [isDragging, setIsDragging] = useState(false);
  const [positions, setPositions] = useState([]); // Default empty array instead of mock data
  const [editingId, setEditingId] = useState(null);
  const [editFormData, setEditFormData] = useState({ shares: '', avgCost: '' });
  
  // Cash balance state
  const [availableCash, setAvailableCash] = useState(0);
  const [isEditingCash, setIsEditingCash] = useState(false);
  const [cashInputValue, setCashInputValue] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [overwriteHoldings, setOverwriteHoldings] = useState(false);
  
  // AI Review state
  const [aiReview, setAiReview] = useState(null);
  const [isLoadingReview, setIsLoadingReview] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  
  // New API fetch function for initial load
  const loadPositions = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/portfolio/${userId}/positions`);
      if (response.ok) {
        const data = await response.json();
        setPositions(data);
      }
    } catch (error) {
       console.error("Failed to load positions from backend", error);
    }
  };

  const loadCashBalance = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/portfolio/${userId}/cash`);
      if (response.ok) {
        const data = await response.json();
        setAvailableCash(data.available_cash);
      }
    } catch (error) {
       console.error("Failed to load cash balance from backend", error);
    }
  };

  // Run once on mount
  React.useEffect(() => {
    loadPositions();
    loadCashBalance();
  }, []);
  
  const fetchPrice = async (ticker) => {
    try {
      const response = await fetch(`http://localhost:8000/api/market/price/${ticker}`);
      if (response.ok) {
        const data = await response.json();
        return data.currentPrice;
      }
    } catch (e) {
      console.error(`Failed to fetch live price for ${ticker}`, e);
    }
    return null; /* Fallback */
  };

  const positionsSignature = React.useMemo(() => {
    // Computes a stable signature based only on holdings and cost-basis, ignoring live price fluctuations
    return JSON.stringify(positions.map(p => `${p.ticker}-${p.shares}-${p.avgCost}`).sort());
  }, [positions]);

  React.useEffect(() => {
    if (positions.length === 0) return;
    
    const updatePrices = async () => {
      let changed = false;
      const updatedPositions = await Promise.all(
        positions.map(async (pos) => {
          if (pos.currentPrice === null) {
            const livePrice = await fetchPrice(pos.ticker);
            if (livePrice !== null) {
              changed = true;
              return { ...pos, currentPrice: livePrice };
            }
          }
          return pos;
        })
      );
      if (changed) {
        setPositions(updatedPositions);
      }
    };
    updatePrices();

    const fetchAiReview = async () => {
      setIsLoadingReview(true);
      try {
        const response = await fetch(`http://localhost:8000/api/portfolio/${userId}/review`);
        if (response.ok) {
          const data = await response.json();
          setAiReview(data.review);
          // Cache the response locked to the current portfolio signature
          sessionStorage.setItem(`ai_review_${userId}`, JSON.stringify({ review: data.review, sig: positionsSignature }));
        }
      } catch (err) {
        console.error("Failed to load AI review", err);
        setAiReview("<p>Could not connect to AI services.</p>");
      } finally {
        setIsLoadingReview(false);
      }
    };
    
    // Check for a valid cached AI review before initiating the heavy backend fetch
    const cached = sessionStorage.getItem(`ai_review_${userId}`);
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        if (parsed.sig === positionsSignature) {
           setAiReview(parsed.review);
           return;
        }
      } catch (e) {}
    }

    fetchAiReview();
  }, [positionsSignature, userId]); // Dependency on signature cleanly manages remounts and avoids infinite loops

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  // Dynamically compute aggregated portfolio metrics
  const { totalPortfolio, totalReturnAmt, totalReturnPct } = React.useMemo(() => {
    let currentVal = 0;
    let costBasisVal = 0;

    positions.forEach(pos => {
      const safeCurrent = pos.currentPrice ?? pos.avgCost; // Fallback to neutral if loading
      currentVal += safeCurrent * pos.shares;
      costBasisVal += pos.avgCost * pos.shares;
    });

    const netRetAmt = currentVal - costBasisVal;
    // Prevent Division By Zero on empty portfolios
    const netRetPct = costBasisVal > 0 ? (netRetAmt / costBasisVal) * 100 : 0; 
    
    return {
      totalPortfolio: currentVal,
      totalReturnAmt: netRetAmt,
      totalReturnPct: netRetPct
    };
  }, [positions]);

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e?.dataTransfer?.files[0] || e?.target?.files?.[0];
    
    if (file && file.type === 'text/csv') {
      setIsUploading(true);
      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("overwrite", overwriteHoldings);

        const res = await fetch(`http://localhost:8000/api/portfolio/${userId}/positions/upload`, {
          method: 'POST',
          body: formData
        });

        if (res.ok) {
          const data = await res.json();
          if (data.count > 0) {
              alert(`Successfully extracted and added ${data.count} positions from your file!`);
              await loadPositions();
          } else {
              alert("The AI couldn't find any valid stock positions in that file.");
          }
          if (e.target) e.target.value = null; // Reset input
        } else {
          alert("Backend AI processing failed.");
        }
      } catch (err) {
        console.error("Upload error", err);
        alert("Error connecting to the AI parsing server.");
      } finally {
        setIsUploading(false);
      }
    } else if (file) {
      alert("Please upload a valid .csv file.");
    }
  };

  const handleFileChange = (e) => {
    handleDrop(e);
  };

  const handleCashEditStart = () => {
    setCashInputValue(availableCash.toString());
    setIsEditingCash(true);
  };

  const handleCashSave = async () => {
    const newCash = parseFloat(cashInputValue);
    if (!isNaN(newCash) && newCash >= 0) {
      try {
        const res = await fetch(`http://localhost:8000/api/portfolio/${userId}/cash`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ available_cash: newCash })
        });
        if (res.ok) {
          setAvailableCash(newCash);
        } else {
          alert("Failed to save cash balance.");
        }
      } catch (err) {
        alert("API error updating cash.");
      }
    }
    setIsEditingCash(false);
  };

  const handleCashKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleCashSave();
    } else if (e.key === 'Escape') {
      setIsEditingCash(false);
    }
  };

  const handleEditClick = (pos) => {
    setEditingId(pos.id);
    setEditFormData({
      shares: pos.shares,
      avgCost: pos.avgCost
    });
  };

  const handleCancelClick = () => {
    setEditingId(null);
  };

  const handleEditFormChange = (e) => {
    const { name, value } = e.target;
    setEditFormData({ ...editFormData, [name]: value });
  };

  const handleSaveClick = async (pos) => {
    try {
      const res = await fetch(`http://localhost:8000/api/portfolio/${userId}/positions/${pos.ticker}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: pos.ticker,
          shares: parseFloat(editFormData.shares),
          avg_cost: parseFloat(editFormData.avgCost)
        })
      });
      if (res.ok) {
        setPositions(
          positions.map((p) =>
            p.id === pos.id ? { ...p, shares: parseFloat(editFormData.shares), avgCost: parseFloat(editFormData.avgCost) } : p
          )
        );
        setEditingId(null);
      } else {
        alert("Failed to save changes to backend!");
      }
    } catch (err) {
      console.error(err);
      alert("API Error updating position.");
    }
  };

  const handleDeleteClick = async (pos) => {
    try {
      const res = await fetch(`http://localhost:8000/api/portfolio/${userId}/positions/${pos.ticker}`, {
        method: 'DELETE'
      });
      if (res.ok) {
         setPositions(positions.filter(p => p.id !== pos.id));
      } else {
         alert("Failed to delete position on backend!");
      }
    } catch (err) {
       console.error(err);
       alert("API Error deleting position.");
    }
  };

  return (
    <div className="dashboard-container">
      <div className="summary-cards">
        <div className="card glass-panel stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-primary)' }}>
            <Briefcase size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Total Portfolio</span>
            <h2 className="stat-value">
              ${totalPortfolio.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h2>
          </div>
        </div>

        <div className="card glass-panel stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: 'var(--color-success)' }}>
            <TrendingUp size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">All Time Return</span>
            <h2 className={`stat-value ${totalReturnAmt >= 0 ? 'text-success' : 'text-danger'}`}>
              {totalReturnAmt >= 0 ? '+' : ''}{totalReturnPct.toFixed(2)}%
            </h2>
          </div>
        </div>

        <div className="card glass-panel stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' }}>
            <DollarSign size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Available Cash (Editable)</span>
            {isEditingCash ? (
              <div className="input-prefix-wrapper" style={{ marginTop: '4px' }}>
                <span>$</span>
                <input 
                  type="number" 
                  value={cashInputValue} 
                  onChange={(e) => setCashInputValue(e.target.value)}
                  onBlur={handleCashSave}
                  onKeyDown={handleCashKeyDown}
                  className="inline-edit-input"
                  style={{ width: '120px', fontSize: '1.25rem', fontWeight: 600, padding: '2px 8px' }}
                  autoFocus
                />
              </div>
            ) : (
              <h2 className="stat-value" onClick={handleCashEditStart} style={{ cursor: 'pointer' }} title="Click to edit">
                ${availableCash.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </h2>
            )}
          </div>
        </div>
      </div>

      <div className="dashboard-grid main-grid">
        <div className="card glass-panel positions-table-card">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Current Holdings</h3>
            <button 
              className="action-btn" 
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(59, 130, 246, 0.1)', color: 'var(--accent-primary)', padding: '0.5rem 1rem', borderRadius: '8px' }}
              onClick={() => setIsImportOpen(!isImportOpen)}
            >
              <UploadCloud size={16} /> Import CSV {isImportOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>

          {isImportOpen && (
            <div className="compact-upload-zone" style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(255,255,255,0.02)' }}>
              <div className="upload-options" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}>
                <label className="toggle-switch">
                  <input 
                    type="checkbox" 
                    checked={overwriteHoldings}
                    onChange={(e) => setOverwriteHoldings(e.target.checked)}
                  />
                  <span className="slider round"></span>
                </label>
                <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  {overwriteHoldings ? "Overwrite holdings" : "Add to holdings"}
                </span>
              </div>
              <div 
                className={`upload-zone ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                style={{ padding: '2rem 1rem', minHeight: '120px' }}
              >
                <UploadCloud size={32} className="upload-icon" />
                <p style={{ margin: '0.5rem 0 0 0', fontWeight: 500 }}>{isUploading ? "AI is processing..." : "Drag & Drop Brokerage CSV here"}</p>
                <input 
                  type="file" 
                  accept=".csv" 
                  className="file-input-hidden" 
                  onChange={handleFileChange}
                  disabled={isUploading}
                />
              </div>
            </div>
          )}

          <div className="table-responsive">
            <table className="positions-table">
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Shares</th>
                  <th>Avg Cost</th>
                  <th>Current Price</th>
                  <th>Total Return</th>
                  <th className="action-col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {positions.map(pos => {
                  const safeCurrent = pos.currentPrice ?? pos.avgCost; // Fallback if loading
                  const totalReturn = (safeCurrent - pos.avgCost) * pos.shares;
                  const isPositive = totalReturn >= 0;
                  const isEditing = editingId === pos.id;

                  return (
                    <tr key={pos.id}>
                      <td className="fw-500">{pos.ticker}</td>
                      <td>
                        {isEditing ? (
                          <input type="number" name="shares" value={editFormData.shares} onChange={handleEditFormChange} className="inline-edit-input" />
                        ) : (
                          pos.shares
                        )}
                      </td>
                      <td>
                        {isEditing ? (
                          <div className="input-prefix-wrapper">
                            <span>$</span>
                            <input type="number" name="avgCost" value={editFormData.avgCost} onChange={handleEditFormChange} className="inline-edit-input" />
                          </div>
                        ) : (
                          `$${pos.avgCost.toFixed(2)}`
                        )}
                      </td>
                      <td>{pos.currentPrice ? `$${pos.currentPrice.toFixed(2)}` : 'Loading...'}</td>
                      <td className={isPositive ? 'text-success' : 'text-danger'}>
                        {isPositive ? '+' : ''}${totalReturn.toFixed(2)}
                      </td>
                      <td className="action-col">
                        {isEditing ? (
                          <div className="action-buttons">
                            <button onClick={() => handleSaveClick(pos)} className="action-btn save-btn" title="Save"><Check size={16} /></button>
                            <button onClick={handleCancelClick} className="action-btn cancel-btn" title="Cancel"><X size={16} /></button>
                          </div>
                        ) : (
                          <div className="action-buttons">
                            <button onClick={() => handleEditClick(pos)} className="action-btn edit-btn" title="Edit"><Edit2 size={16} /></button>
                            <button onClick={() => handleDeleteClick(pos)} className="action-btn delete-btn" title="Delete"><Trash2 size={16} /></button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card glass-panel ai-review-card">
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={20} className="text-accent" />
            <h3 style={{ margin: 0 }}>AI Portfolio Review</h3>
          </div>
          
          <div className="ai-review-content" style={{ padding: '1.5rem', height: 'calc(100% - 60px)', overflowY: 'auto' }}>
            {isLoadingReview ? (
               <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
                 <Sparkles className="spin" size={24} style={{ marginBottom: '1rem', opacity: 0.5 }} />
                 <p>Analyzing your holdings...</p>
               </div>
            ) : (
               <div className="markdown-body" dangerouslySetInnerHTML={{ __html: aiReview || "<p>Add positions to see your review.</p>" }} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
