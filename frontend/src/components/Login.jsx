import React, { useState } from 'react';
import API_BASE from '../config.js';
import { Mail, ArrowRight } from 'lucide-react';
import './Login.css';

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !email.includes('@')) {
      setError("Please enter a valid email address.");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      
      if (response.ok) {
        const data = await response.json();
        onLogin(data.user_id);
      } else {
        const errData = await response.json();
        setError(errData.detail || "Authentication failed.");
      }
    } catch (err) {
      console.error(err);
      setError("Cannot connect to server. Is the backend running?");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container fade-in">
      <div className="login-card glass-panel">
        <div className="login-header">
          <h2>Memory<span>Vest</span></h2>
          <p>Your intelligent investing companion.</p>
        </div>
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <div className="input-icon">
              <Mail size={18} />
            </div>
            <input 
              type="email" 
              placeholder="Enter your email address" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>
          
          {error && <div className="login-error">{error}</div>}
          
          <button type="submit" className="login-submit-btn" disabled={isLoading}>
            {isLoading ? "Authenticating..." : "Continue to Dashboard"} <ArrowRight size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
