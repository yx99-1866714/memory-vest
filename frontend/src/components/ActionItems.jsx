import React, { useState, useEffect } from 'react';
import { Target, TrendingUp, Sparkles, Loader } from 'lucide-react';
import './ActionItems.css';

export default function ActionItems({ userId }) {
  const [actionItems, setActionItems] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchActionItems = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`http://localhost:8000/api/portfolio/${userId}/action-items`);
        if (response.ok) {
          const data = await response.json();
          setActionItems(data.action_items);
        } else {
          setActionItems("<p>Failed to load your action items.</p>");
        }
      } catch (err) {
        console.error("Error fetching action items:", err);
        setActionItems("<p>Could not connect to AI services.</p>");
      } finally {
        setIsLoading(false);
      }
    };

    fetchActionItems();
  }, [userId]);

  return (
    <div className="action-items-container slide-up">
      <div className="card glass-panel action-items-main-card">
        <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2rem' }}>
          <div className="icon-badge">
            <Target size={24} className="text-accent" />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.5rem' }}>AI Watchlist</h2>
            <p className="subtitle" style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)' }}>
              Tailored market themes to monitor based on your current holdings.
            </p>
          </div>
        </div>

        <div className="action-items-content">
          {isLoading ? (
            <div className="loading-state">
              <Sparkles className="spin" size={32} />
              <p>Analyzing market data and generating your watchlist...</p>
            </div>
          ) : (
            <div className="markdown-body custom-action-formatting" dangerouslySetInnerHTML={{ __html: actionItems }} />
          )}
        </div>
      </div>
    </div>
  );
}
