import React, { useState, useEffect, useRef } from 'react';
import { Target, Sparkles, X } from 'lucide-react';
import './ActionItems.css';

// Module-level singleton — survives component unmount/remount
// This prevents duplicate sync requests when rapidly switching tabs
const syncState = {}; // keyed by userId

export default function ActionItems({ userId }) {
  const [items, setItems] = useState([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  useEffect(() => {
    const loadAndSync = async () => {
      // Phase 1: Always load stored items instantly from DB
      try {
        const res = await fetch(`http://localhost:8000/api/portfolio/${userId}/action-items`);
        if (mountedRef.current && res.ok) {
          const data = await res.json();
          setItems(data.action_items || []);
        }
      } catch (err) {
        console.error("Failed to load stored action items:", err);
      }

      if (mountedRef.current) setInitialized(true);

      // Phase 2: Background sync — skip if one is already in-flight for this user
      if (syncState[userId]) {
        // A sync is already running. Subscribe to its result so we pick up new items.
        if (mountedRef.current) setIsSyncing(true);
        syncState[userId].then(newItems => {
          if (mountedRef.current && newItems.length > 0) {
            setItems(prev => [...prev, ...newItems]);
          }
        }).finally(() => {
          if (mountedRef.current) setIsSyncing(false);
        });
        return;
      }

      // Start a new sync and register the promise so other mounts can subscribe to it
      if (mountedRef.current) setIsSyncing(true);

      const syncPromise = fetch(`http://localhost:8000/api/portfolio/${userId}/action-items/sync`, {
        method: 'POST',
      }).then(async res => {
        if (!res.ok) return [];
        const data = await res.json();
        return (data.new_items || []).map((item, i) => ({
          id: `new_${Date.now()}_${i}`,
          ...item
        }));
      }).catch(err => {
        console.error("Failed to sync new action items:", err);
        return [];
      }).finally(() => {
        // Clear after completion so future visits can re-check
        delete syncState[userId];
        if (mountedRef.current) setIsSyncing(false);
      });

      // Register globally so any concurrent mount can subscribe, not duplicate
      syncState[userId] = syncPromise;

      const newItems = await syncPromise;
      if (mountedRef.current && newItems.length > 0) {
        setItems(prev => [...prev, ...newItems]);
      }
    };

    loadAndSync();
    // Note: no cleanup cancels the sync — we want it to complete even if the user navigates away
    // so that items are saved to DB and visible on return.
  }, [userId]);

  const handleDismiss = async (item) => {
    setItems(prev => prev.filter(i => i !== item));
    if (item.id && typeof item.id === 'number') {
      try {
        await fetch(`http://localhost:8000/api/portfolio/${userId}/action-items/${item.id}`, {
          method: 'DELETE',
        });
      } catch (err) {
        console.error("Failed to delete action item:", err);
      }
    }
  };

  const showEmpty = initialized && items.length === 0 && !isSyncing;

  return (
    <div className="action-items-container slide-up">
      <div className="card glass-panel action-items-main-card">
        <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2rem', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div className="icon-badge">
              <Target size={24} className="text-accent" />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.5rem' }}>Action Items</h2>
              <p className="subtitle" style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)' }}>
                Directives you have asked MemoryVest to monitor.
              </p>
            </div>
          </div>
          {isSyncing && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              <Sparkles size={14} className="spin" />
              Checking for new items...
            </div>
          )}
        </div>

        <div className="action-items-content">
          {showEmpty ? (
            <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>
              You don't have any active Action Items. Chat with me and tell me what you'd like me to monitor!
            </p>
          ) : (
            <div className="custom-action-formatting">
              {items.map((item, idx) => {
                // Inject timestamp inside the <details> block, right after </summary>
                const ts = item.created_at
                  ? new Date(item.created_at).toLocaleString(undefined, {
                      month: 'short', day: 'numeric', year: 'numeric',
                      hour: 'numeric', minute: '2-digit'
                    })
                  : null;
                const htmlWithTimestamp = ts
                  ? item.description_html.replace(
                      '</summary>',
                      `</summary><span class="action-item-timestamp">Requested ${ts}</span>`
                    )
                  : item.description_html;

                return (
                  <div key={item.id ?? idx} className="action-item-wrapper">
                    <div dangerouslySetInnerHTML={{ __html: htmlWithTimestamp }} />
                    <button
                      className="dismiss-btn"
                      onClick={() => handleDismiss(item)}
                      title="Dismiss this action item"
                    >
                      <X size={14} />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
