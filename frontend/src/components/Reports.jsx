import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import { FileText, Calendar, Loader, Clock, Inbox, Sparkles, Trash2, Bot, User, Send } from 'lucide-react';
import './Reports.css';

// Module-level singleton — keeps generation alive across tab switches
const generationState = {}; // { [userId]: Promise<report> | null }

// ── Mini report chat panel ─────────────────────────────────────────────────────
function ReportChatPanel({ userId, report }) {
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [welcomed, setWelcomed] = useState(false);
  const messagesEndRef = useRef(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, chatLoading]);

  // Fetch welcome message whenever the selected report changes
  useEffect(() => {
    if (!report) return;
    setWelcomed(false);
    setChatMessages([]);

    const fetchWelcome = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/reports/${userId}/${report.report_id}/chat-welcome`);
        if (res.ok && mountedRef.current) {
          const data = await res.json();
          setChatMessages([{ role: 'assistant', text: data.message }]);
          setWelcomed(true);
        }
      } catch (e) {
        console.error('Report chat welcome error:', e);
      }
    };
    fetchWelcome();
  }, [report?.report_id, userId]);

  const handleChatSend = async (e) => {
    e?.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userText = chatInput.trim();
    setChatMessages(prev => [...prev, { role: 'user', text: userText }]);
    setChatInput('');
    setChatLoading(true);

    try {
      const res = await fetch(`http://localhost:8000/api/reports/${userId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userText,
          report_content: report?.report_content || ''
        })
      });
      if (res.ok) {
        const data = await res.json();
        if (mountedRef.current) setChatMessages(prev => [...prev, { role: 'assistant', text: data.reply }]);
      }
    } catch (e) {
      console.error('Report chat send error:', e);
    } finally {
      if (mountedRef.current) setChatLoading(false);
    }
  };

  return (
    <div className="report-chat-panel glass-panel">
      <div className="report-chat-header">
        <Bot size={16} />
        <span>Discuss this report</span>
      </div>

      <div className="report-chat-messages">
        {chatMessages.map((msg, idx) => (
          <div key={idx} className={`report-chat-msg ${msg.role}`}>
            <div className="report-chat-avatar">
              {msg.role === 'assistant' ? <Bot size={14} /> : <User size={14} />}
            </div>
            <div className="report-chat-bubble">{msg.text}</div>
          </div>
        ))}
        {chatLoading && (
          <div className="report-chat-msg assistant">
            <div className="report-chat-avatar"><Bot size={14} /></div>
            <div className="report-chat-bubble typing-dots">
              <span /><span /><span />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="report-chat-input-row" onSubmit={handleChatSend}>
        <input
          type="text"
          placeholder="Ask about this report or share feedback…"
          value={chatInput}
          onChange={e => setChatInput(e.target.value)}
          disabled={chatLoading}
        />
        <button type="submit" disabled={!chatInput.trim() || chatLoading}>
          <Send size={15} />
        </button>
      </form>
    </div>
  );
}

// ── Main Reports component ─────────────────────────────────────────────────────
export default function Reports({ userId }) {
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(!!generationState[userId]);
  const [error, setError] = useState(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const fetchReports = useCallback(async (autoSelect = true) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/api/reports/${userId}`);
      if (res.ok) {
        const data = await res.json();
        if (mountedRef.current) {
          setReports(data);
          if (autoSelect && data.length > 0) setSelectedReport(data[0]);
        }
      } else {
        if (mountedRef.current) setError("Failed to fetch reports. Is the backend running?");
      }
    } catch (err) {
      console.error(err);
      if (mountedRef.current) setError("Error connecting to the backend server.");
    } finally {
      if (mountedRef.current) setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchReports();
    if (generationState[userId]) {
      if (mountedRef.current) setIsGenerating(true);
      generationState[userId].then(newReport => {
        if (mountedRef.current && newReport) {
          setReports(prev => [newReport, ...prev]);
          setSelectedReport(newReport);
        }
      }).finally(() => {
        if (mountedRef.current) setIsGenerating(false);
      });
    }
  }, [userId]);

  const handleGenerate = async () => {
    if (generationState[userId]) return;
    if (mountedRef.current) setIsGenerating(true);

    const genPromise = fetch(`http://localhost:8000/api/reports/${userId}/generate`, {
      method: 'POST'
    }).then(async res => {
      if (!res.ok) { console.error("Report generation failed"); return null; }
      return res.json();
    }).catch(err => { console.error("Report generation error:", err); return null; })
      .finally(() => {
        delete generationState[userId];
        if (mountedRef.current) setIsGenerating(false);
      });

    generationState[userId] = genPromise;
    const newReport = await genPromise;
    if (mountedRef.current && newReport) {
      setReports(prev => [newReport, ...prev]);
      setSelectedReport(newReport);
    }
  };

  const handleDelete = async (report, e) => {
    e.stopPropagation();
    setReports(prev => prev.filter(r => r.report_id !== report.report_id));
    if (selectedReport?.report_id === report.report_id) setSelectedReport(null);
    try {
      await fetch(`http://localhost:8000/api/reports/${userId}/${report.report_id}`, { method: 'DELETE' });
    } catch (err) {
      console.error("Failed to delete report:", err);
      fetchReports(false);
    }
  };

  return (
    <div className="reports-container fade-in">
      {/* Sidebar */}
      <div className="reports-sidebar glass-panel slide-right">
        <div className="reports-sidebar-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3><FileText size={18} /> Report History</h3>
            <button className="generate-btn" onClick={handleGenerate} disabled={isGenerating}
              title={isGenerating ? "Generating report..." : "Generate New AI Report"}>
              {isGenerating ? <Loader size={16} className="spin" /> : <Sparkles size={16} />}
            </button>
          </div>
          {isGenerating && (
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0.5rem 0 0 0' }}>
              Generating… feel free to browse other sections.
            </p>
          )}
        </div>

        {isLoading ? (
          <div className="reports-loading"><Loader className="spin" size={24} /><p>Loading history...</p></div>
        ) : error ? (
          <div className="reports-error">{error}</div>
        ) : reports.length === 0 ? (
          <div className="reports-empty">
            <Inbox size={32} />
            <p>No reports generated yet.</p>
            <button className="btn-primary" onClick={handleGenerate} disabled={isGenerating}>
              {isGenerating ? "Generating..." : "Generate Your First Report"}
            </button>
          </div>
        ) : (
          <div className="reports-list">
            {reports.map((report) => {
              const date = new Date(report.generated_at);
              return (
                <div key={report.report_id}
                  className={`report-list-item ${selectedReport?.report_id === report.report_id ? 'active' : ''}`}
                  onClick={() => setSelectedReport(report)}>
                  <div className="report-item-icon"><Calendar size={16} /></div>
                  <div className="report-item-details">
                    <div className="report-item-date">{date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}</div>
                    <div className="report-item-time"><Clock size={12} /> {date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}</div>
                  </div>
                  <button className="report-delete-btn" onClick={(e) => handleDelete(report, e)} title="Delete this report">
                    <Trash2 size={14} />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Viewer + Chat column */}
      <div className="report-viewer-column">
        <div className="report-viewer glass-panel slide-left">
          {isGenerating && reports.length === 0 ? (
            <div className="report-viewer-placeholder">
              <Loader size={40} className="spin" opacity={0.4} />
              <p>Your report is being generated…</p>
            </div>
          ) : selectedReport ? (
            <>
              <div className="report-viewer-header">
                <h2>Insight generated on {new Date(selectedReport.generated_at).toLocaleDateString()}</h2>
                <span className="report-badge">AI Authored</span>
              </div>
              <div className="report-viewer-content markdown-body">
                {selectedReport.report_content ? (
                  <ReactMarkdown rehypePlugins={[rehypeRaw]}>{selectedReport.report_content}</ReactMarkdown>
                ) : (
                  <div className="report-content-empty">
                    <p>No content available for this report.</p>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="report-viewer-placeholder">
              <FileText size={48} opacity={0.2} />
              <p>Select a report from the sidebar to view insights.</p>
            </div>
          )}
        </div>

        {/* Contextual chat panel — only when a report is selected */}
        {selectedReport && <ReportChatPanel userId={userId} report={selectedReport} />}
      </div>
    </div>
  );
}
