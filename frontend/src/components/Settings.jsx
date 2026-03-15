import React, { useState, useEffect } from 'react';
import { Info, Save, Mail, BarChart2, Shield, Settings2, Clock } from 'lucide-react';
import './Settings.css';
import API_BASE from '../config.js';

export default function Settings({ userId }) {
  const [profile, setProfile] = useState({
    email: 'user@example.com',
    experienceLevel: 'intermediate',
    riskTolerance: 'moderate',
    interests: 'AI, Clean Energy, Web3',
    reportFrequency: 'daily'
  });

  useEffect(() => {
    const fetchProfile = async () => {
      try {
      const response = await fetch(`${API_BASE}/api/profile/${userId}`);
        if (response.ok) {
          const data = await response.json();
          setProfile(data);
        }
      } catch (e) {
        console.error("Failed to load profile", e);
      }
    };
    fetchProfile();
  }, []);

  const handleChange = (e) => {
    setProfile({ ...profile, [e.target.name]: e.target.value });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE}/api/profile/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: profile.email,
          experience_level: profile.experienceLevel,
          risk_tolerance: profile.riskTolerance,
          interests: profile.interests,
          report_frequency: profile.reportFrequency
        })
      });
      if (response.ok) {
        alert("Profile settings saved successfully!");
      } else {
        alert("Failed to save profile settings.");
      }
    } catch (error) {
       console.error("Save profile error", error);
       alert("Error connecting to server to save profile.");
    }
  };

  return (
    <div className="settings-container">
      <div className="ai-notice slide-up">
        <div className="ai-notice-icon">
          <Info size={24} />
        </div>
        <div className="ai-notice-text">
          <h3>Did you know?</h3>
          <p>You don't have to fill this out manually. Just open the <strong>Chat</strong> and tell MemoryVest about your preferences, and we will automatically update this profile for you!</p>
        </div>
      </div>

      <div className="card glass-panel settings-card slide-up" style={{ animationDelay: '0.1s' }}>
        <div className="card-header">
          <h3>Profile Preferences</h3>
          <p className="subtitle">Manage what MemoryVest knows about you to personalize your reports.</p>
        </div>

        <form onSubmit={handleSave} className="settings-form">
          <div className="form-group">
            <label><Mail size={16} /> Email Address</label>
            <input type="email" name="email" value={profile.email} onChange={handleChange} className="glass-input" />
          </div>

          <div className="form-group">
            <label><BarChart2 size={16} /> Experience Level</label>
            <select name="experienceLevel" value={profile.experienceLevel} onChange={handleChange} className="glass-input">
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="expert">Expert</option>
            </select>
          </div>

          <div className="form-group">
            <label><Shield size={16} /> Risk Tolerance</label>
            <select name="riskTolerance" value={profile.riskTolerance} onChange={handleChange} className="glass-input">
              <option value="low">Low (Conservative)</option>
              <option value="moderate">Moderate</option>
              <option value="high">High (Aggressive)</option>
            </select>
          </div>

          <div className="form-group">
            <label><Clock size={16} /> Report Frequency</label>
            <select name="reportFrequency" value={profile.reportFrequency} onChange={handleChange} className="glass-input">
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          <div className="form-group full-width">
            <label><Settings2 size={16} /> Tracked Interests & Themes</label>
            <input type="text" name="interests" value={profile.interests} onChange={handleChange} className="glass-input" placeholder="e.g. AI, Space, Tech, Biotech..." />
            <small className="form-hint">Separate multiple interests with commas.</small>
          </div>

          <div className="form-actions full-width">
            <button type="submit" className="btn-primary">
              <Save size={18} /> Save Preferences
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
