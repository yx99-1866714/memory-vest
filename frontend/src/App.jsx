import React, { useState } from 'react';
import Cookies from 'js-cookie';
import './App.css';
import { LayoutDashboard, MessageSquare, FileText, Settings as SettingsIcon, Activity, LogOut, Target } from 'lucide-react';
import Chat from './components/Chat';
import Dashboard from './components/Dashboard';
import Settings from './components/Settings';
import Login from './components/Login';
import Reports from './components/Reports';
import ActionItems from './components/ActionItems';

function App() {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [userId, setUserId] = useState(Cookies.get('memoryvest_user_id') || null);

  const handleLogin = (id) => {
    Cookies.set('memoryvest_user_id', id, { expires: 365 });
    setUserId(id);
  };

  const handleLogout = () => {
    Cookies.remove('memoryvest_user_id');
    setUserId(null);
  };

  if (!userId) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="app-container fade-in">
      <div className="layout">
        <aside className="sidebar">
          <div className="logo">
            <h2>Memory<span>Vest</span></h2>
          </div>
          <nav>
            <ul>
              <li className={activeTab === 'Dashboard' ? 'active' : ''} onClick={() => setActiveTab('Dashboard')}>
                <LayoutDashboard size={20} /> Dashboard
              </li>
              <li className={activeTab === 'Action Items' ? 'active' : ''} onClick={() => setActiveTab('Action Items')}>
                <Target size={20} /> Action Items
              </li>
              <li className={activeTab === 'Chat' ? 'active' : ''} onClick={() => setActiveTab('Chat')}>
                <MessageSquare size={20} /> Chat & Trade
              </li>
              <li className={activeTab === 'Reports' ? 'active' : ''} onClick={() => setActiveTab('Reports')}>
                <FileText size={20} /> Reports
              </li>
              <li className={activeTab === 'Settings' ? 'active' : ''} onClick={() => setActiveTab('Settings')}>
                <SettingsIcon size={20} /> User Profile
              </li>
            </ul>
          </nav>
          
          <div className="sidebar-footer" style={{ marginTop: 'auto', padding: '1rem' }}>
            <button 
              onClick={handleLogout} 
              className="logout-btn" 
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.9rem', width: '100%', padding: '0.75rem', borderRadius: '8px', transition: 'background-color 0.2s', marginTop: '1rem' }}
              onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.05)'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
            >
              <LogOut size={18} /> Sign Out
            </button>
          </div>
        </aside>

        {/* Main Content placeholder */}
        <main className="main-content">
          <header className="topbar glass-panel">
            <h1>{activeTab}</h1>
            <div className="status-indicator" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
              <Activity size={16} color="var(--color-success)" />
              <span>System Online</span>
            </div>
          </header>
          <div className="content-area slide-up" key={activeTab}>
            {activeTab === 'Dashboard' && (
              <Dashboard userId={userId} />
            )}
            
            {activeTab === 'Action Items' && (
              <ActionItems userId={userId} />
            )}
            
            {activeTab === 'Chat' && (
              <Chat userId={userId} />
            )}
            
            {activeTab === 'Reports' && (
              <Reports userId={userId} />
            )}
            
            {activeTab === 'Settings' && (
              <Settings userId={userId} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
