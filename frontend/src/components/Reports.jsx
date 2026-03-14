import React, { useState, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import { FileText, Calendar, Loader, Clock, Inbox, Plus, Sparkles } from 'lucide-react';
import './Reports.css';

export default function Reports({ userId }) {
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);

  const fetchReports = useCallback(async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await fetch(`http://localhost:8000/api/reports/${userId}`);
        if (res.ok) {
          const data = await res.json();
          setReports(data);
          if (data.length > 0) {
            setSelectedReport(data[0]); // Auto-select the most recent report
          }
        } else {
          setError("Failed to fetch reports. Is the backend running?");
        }
      } catch (err) {
        console.error(err);
        setError("Error connecting to the backend server.");
      } finally {
        setIsLoading(false);
      }
    }, [userId]);

  useEffect(() => {
    fetchReports();
  }, [userId]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const res = await fetch(`http://localhost:8000/api/reports/${userId}/generate`, {
        method: 'POST'
      });
      if (res.ok) {
        await fetchReports();
      } else {
        const errorData = await res.json();
        alert(`Failed to generate report: ${errorData.detail}`);
      }
    } catch (err) {
      console.error(err);
      alert('Error connecting to the backend to generate report.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="reports-container fade-in">
      <div className="reports-sidebar glass-panel slide-right">
        <div className="reports-sidebar-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3><FileText size={18} /> Report History</h3>
            <button 
              className="generate-btn" 
              onClick={handleGenerate} 
              disabled={isGenerating}
              title="Generate New AI Report"
            >
              {isGenerating ? <Loader size={16} className="spin" /> : <Sparkles size={16} />}
            </button>
          </div>
        </div>
        
        {isLoading ? (
          <div className="reports-loading">
            <Loader className="spin" size={24} />
            <p>Loading history...</p>
          </div>
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
                <div 
                  key={report.report_id} 
                  className={`report-list-item ${selectedReport?.report_id === report.report_id ? 'active' : ''}`}
                  onClick={() => setSelectedReport(report)}
                >
                  <div className="report-item-icon">
                    <Calendar size={16} />
                  </div>
                  <div className="report-item-details">
                    <div className="report-item-date">{date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}</div>
                    <div className="report-item-time"><Clock size={12} /> {date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="report-viewer glass-panel slide-left">
        {selectedReport ? (
          <>
            <div className="report-viewer-header">
              <h2>Insight generated on {new Date(selectedReport.generated_at).toLocaleDateString()}</h2>
              <span className="report-badge">AI Authored</span>
            </div>
            <div className="report-viewer-content markdown-body">
              {selectedReport.report_content ? (
                <ReactMarkdown rehypePlugins={[rehypeRaw]}>
                  {selectedReport.report_content}
                </ReactMarkdown>
              ) : (
                <div className="report-content-empty">
                  <p>Warning: This specific report metadata was saved before the body text persistence migration. No content available.</p>
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
    </div>
  );
}
