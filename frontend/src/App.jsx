import { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { fetchErrors, fetchActiveErrors, fetchStats, fetchHealth, dismissError, dismissAllErrors, WebSocketManager } from './services/api';
import logoImage from './assets/logo.png';

// ===== SVG Icons =====

const IconClipboard = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
    <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
  </svg>
);

const IconAlertTriangle = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);

const IconMonitor = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
    <line x1="8" y1="21" x2="16" y2="21" />
    <line x1="12" y1="17" x2="12" y2="21" />
  </svg>
);

const IconFile = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
  </svg>
);

const IconActivity = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
);

const IconX = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

const IconCheckCircle = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </svg>
);

// ===== Utility Components =====

/**
 * Formats AI response text with proper markdown-like rendering
 */
function FormattedContent({ text }) {
  if (!text) return null;

  // Process the text to handle code blocks and formatting
  const formatText = (content) => {
    const parts = [];
    let remaining = content;
    let key = 0;

    // Handle code blocks first
    const codeBlockRegex = /```(\w*)\n?([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      // Add text before the code block
      if (match.index > lastIndex) {
        const beforeText = content.slice(lastIndex, match.index);
        parts.push(...formatInlineText(beforeText, key));
        key += 100;
      }

      // Add the code block
      const language = match[1] || 'code';
      const code = match[2].trim();
      parts.push(
        <pre key={`code-${key++}`} className="code-block">
          <div className="code-header">{language.toUpperCase()}</div>
          <code>{code}</code>
        </pre>
      );

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text after the last code block
    if (lastIndex < content.length) {
      parts.push(...formatInlineText(content.slice(lastIndex), key));
    }

    return parts;
  };

  // Format inline text (bold, numbered lists, line breaks)
  const formatInlineText = (text, startKey = 0) => {
    let key = startKey;

    // Split by line breaks and process each line
    const lines = text.split('\n');
    const elements = [];

    lines.forEach((line, index) => {
      const trimmedLine = line.trim();

      if (!trimmedLine) {
        // Empty line - add spacing
        if (index > 0) {
          elements.push(<br key={`br-${key++}`} />);
        }
        return;
      }

      // Check for numbered list items (1. or 2. etc)
      const listMatch = trimmedLine.match(/^(\d+)\.\s+(.+)/);
      if (listMatch) {
        elements.push(
          <div key={`list-${key++}`} className="list-item">
            <span className="list-number">{listMatch[1]}.</span>
            <span>{formatBoldText(listMatch[2])}</span>
          </div>
        );
        return;
      }

      // Check for bullet points
      if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ')) {
        elements.push(
          <div key={`bullet-${key++}`} className="list-item">
            <span className="list-bullet">-</span>
            <span>{formatBoldText(trimmedLine.slice(2))}</span>
          </div>
        );
        return;
      }

      // Regular text line
      elements.push(
        <p key={`p-${key++}`} style={{ margin: '0.25rem 0' }}>
          {formatBoldText(trimmedLine)}
        </p>
      );
    });

    return elements;
  };

  // Handle bold text (**text**)
  const formatBoldText = (text) => {
    const parts = [];
    const boldRegex = /\*\*(.+?)\*\*/g;
    let lastIndex = 0;
    let match;
    let key = 0;

    while ((match = boldRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }
      parts.push(<strong key={`bold-${key++}`}>{match[1]}</strong>);
      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  return <div className="formatted-content">{formatText(text)}</div>;
}

// ===== Components =====

function Header({ isConnected }) {
  return (
    <header className="header">
      <div className="container header-content">
        <div className="logo">
          <img src={logoImage} alt="AIDEN Labs" className="logo-image" />
          <span className="logo-text">AIDEN Labs</span>
        </div>

        <nav className="nav">
          <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Dashboard
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            History
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Settings
          </NavLink>
        </nav>

        <div className="connection-status">
          <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
          <span>{isConnected ? 'Live' : 'Disconnected'}</span>
        </div>
      </div>
    </header>
  );
}

function StatsGrid({ stats }) {
  return (
    <div className="stats-grid">
      <div className="card stat-card">
        <div className="stat-icon">
          <IconAlertTriangle />
        </div>
        <div className="stat-value">{stats.total_errors || 0}</div>
        <div className="stat-label">Total Errors</div>
      </div>
      <div className="card stat-card">
        <div className="stat-icon">
          <IconMonitor />
        </div>
        <div className="stat-value">{stats.devices_count || 0}</div>
        <div className="stat-label">Devices Monitored</div>
      </div>
      <div className="card stat-card">
        <div className="stat-icon">
          <IconFile />
        </div>
        <div className="stat-value">{stats.watched_files?.length || 0}</div>
        <div className="stat-label">Active Log Files</div>
      </div>
      <div className="card stat-card">
        <div className="stat-icon">
          <IconActivity />
        </div>
        <div className="stat-value" style={{ color: stats.watcher_running ? 'var(--color-success)' : 'var(--color-error)' }}>
          {stats.watcher_running ? <IconCheckCircle /> : <IconX />}
        </div>
        <div className="stat-label">Watcher {stats.watcher_running ? 'Active' : 'Inactive'}</div>
      </div>
    </div>
  );
}

function ErrorCard({ error, solution, isNew, onDismiss, showDismiss = true }) {
  const [expanded, setExpanded] = useState(false);

  const severityClass = error.severity === 'critical' ? 'critical' :
    error.severity === 'warning' ? 'warning' : '';

  return (
    <div className={`card error-card ${severityClass} ${isNew ? 'new' : ''}`}>
      <div className="card-header">
        <div>
          <span className={`severity-badge ${error.severity}`}>{error.severity}</span>
          <span style={{ marginLeft: '0.5rem', color: 'var(--color-text-muted)' }}>
            {error.device_id}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="error-meta">{new Date(error.timestamp).toLocaleString()}</span>
          {showDismiss && onDismiss && (
            <button
              className="btn btn-dismiss"
              onClick={() => onDismiss(error.id)}
              title="Dismiss error"
            >
              <IconX />
            </button>
          )}
        </div>
      </div>

      <div className="error-line">{error.error_line}</div>

      {solution && (
        <div className="solution">
          <div className="solution-section">
            <div className="solution-label">Root Cause</div>
            <div className="solution-content">
              <FormattedContent text={solution.root_cause} />
            </div>
          </div>
          <div className="solution-section">
            <div className="solution-label">Solution</div>
            <div className="solution-content">
              <FormattedContent text={solution.solution} />
            </div>
          </div>
          {expanded && (
            <>
              <div className="solution-section">
                <div className="solution-label">Impact</div>
                <div className="solution-content">
                  <FormattedContent text={solution.impact} />
                </div>
              </div>
              <div className="solution-section">
                <div className="solution-label">Prevention</div>
                <div className="solution-content">
                  <FormattedContent text={solution.prevention} />
                </div>
              </div>
            </>
          )}
          <button className="btn btn-ghost" onClick={() => setExpanded(!expanded)}>
            {expanded ? 'Show Less' : 'Show More'}
          </button>
        </div>
      )}

      {!solution && (
        <div className="solution">
          <div className="loading">
            <div className="spinner"></div>
          </div>
          <p style={{ textAlign: 'center', fontSize: '0.875rem' }}>Analyzing with AI...</p>
        </div>
      )}
    </div>
  );
}

function ErrorList({ errors, newErrorIds, onDismiss, showDismiss = true }) {
  if (errors.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">
          <IconClipboard />
        </div>
        <h3>No Errors Detected</h3>
        <p>The system is monitoring your log files. Errors will appear here when detected.</p>
      </div>
    );
  }

  return (
    <div className="error-list">
      {errors.map(item => (
        <ErrorCard
          key={item.error.id}
          error={item.error}
          solution={item.solution}
          isNew={newErrorIds.has(item.error.id)}
          onDismiss={onDismiss}
          showDismiss={showDismiss}
        />
      ))}
    </div>
  );
}

function Dashboard({ errors, stats, newErrorIds, onDismiss, onDismissAll }) {
  return (
    <div className="page">
      <div className="container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-xl)' }}>
          <h1>Dashboard</h1>
          {errors.length > 0 && (
            <button className="btn btn-ghost" onClick={onDismissAll}>
              Clear All Errors
            </button>
          )}
        </div>
        <StatsGrid stats={stats} />
        <h2 style={{ marginBottom: 'var(--space-lg)' }}>Recent Errors</h2>
        <ErrorList errors={errors} newErrorIds={newErrorIds} onDismiss={onDismiss} showDismiss={true} />
      </div>
    </div>
  );
}

function History() {
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetchErrors(page, 50)
      .then(data => {
        setErrors(data.errors);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [page]);

  if (loading) {
    return (
      <div className="page">
        <div className="container">
          <div className="loading"><div className="spinner"></div></div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="container">
        <h1 style={{ marginBottom: 'var(--space-xl)' }}>Error History</h1>
        <p style={{ marginBottom: 'var(--space-lg)', color: 'var(--color-text-muted)' }}>
          All errors including dismissed ones are shown here.
        </p>
        <ErrorList errors={errors} newErrorIds={new Set()} showDismiss={false} />
        <div style={{ marginTop: 'var(--space-xl)', display: 'flex', gap: 'var(--space-md)', justifyContent: 'center' }}>
          <button className="btn btn-ghost" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
            Previous
          </button>
          <span style={{ padding: 'var(--space-sm)', color: 'var(--color-text-secondary)' }}>Page {page}</span>
          <button className="btn btn-ghost" onClick={() => setPage(p => p + 1)}>
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

function Settings() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="page">
      <div className="container">
        <h1 style={{ marginBottom: 'var(--space-xl)' }}>Settings</h1>

        <div className="card settings-section" style={{ marginBottom: 'var(--space-xl)' }}>
          <h3 style={{ marginBottom: 'var(--space-lg)' }}>System Status</h3>
          {health ? (
            <div style={{ display: 'grid', gap: 'var(--space-md)' }}>
              <p><strong>Status:</strong> <span style={{ color: 'var(--color-success)' }}>{health.status}</span></p>
              <p><strong>Watcher:</strong> <span style={{ color: health.watcher_running ? 'var(--color-success)' : 'var(--color-error)' }}>{health.watcher_running ? 'Running' : 'Stopped'}</span></p>
              <p><strong>Watch Directory:</strong> <code>{health.watch_directory}</code></p>
            </div>
          ) : (
            <div className="loading"><div className="spinner"></div></div>
          )}
        </div>

        <div className="card settings-section">
          <h3 style={{ marginBottom: 'var(--space-lg)' }}>Configuration</h3>
          <p style={{ color: 'var(--color-text-muted)', marginBottom: 'var(--space-md)' }}>
            Configuration is managed via environment variables. Edit the <code>.env</code> file to change settings.
          </p>
          <ul className="settings-list">
            <li><code>GEMINI_API_KEY</code> - Your Gemini API key</li>
            <li><code>LOG_WATCH_DIR</code> - Directory to monitor for log files</li>
            <li><code>CONTEXT_LINES</code> - Lines of context for AI analysis</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

// ===== Main App =====

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [errors, setErrors] = useState([]);
  const [stats, setStats] = useState({});
  const [newErrorIds, setNewErrorIds] = useState(new Set());

  // Handle dismissing a single error
  const handleDismiss = useCallback(async (errorId) => {
    try {
      await dismissError(errorId);
      setErrors(prev => prev.filter(e => e.error.id !== errorId));
      fetchStats().then(setStats).catch(console.error);
    } catch (err) {
      console.error('Failed to dismiss error:', err);
    }
  }, []);

  // Handle dismissing all errors
  const handleDismissAll = useCallback(async () => {
    try {
      await dismissAllErrors();
      setErrors([]);
      fetchStats().then(setStats).catch(console.error);
    } catch (err) {
      console.error('Failed to dismiss all errors:', err);
    }
  }, []);

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((data) => {
    if (data.type === 'error_update') {
      setErrors(prev => {
        // Update existing or add new
        const existing = prev.findIndex(e => e.error.id === data.data.error.id);
        if (existing >= 0) {
          const updated = [...prev];
          updated[existing] = data.data;
          return updated;
        }
        // Add new error at the top
        setNewErrorIds(ids => new Set([...ids, data.data.error.id]));
        return [data.data, ...prev.slice(0, 49)];
      });

      // Refresh stats
      fetchStats().then(setStats).catch(console.error);
    }
  }, []);

  // Initialize WebSocket and fetch initial data
  useEffect(() => {
    const ws = new WebSocketManager(
      handleMessage,
      () => setIsConnected(true),
      () => setIsConnected(false)
    );
    ws.connect();

    // Fetch initial data - use active errors for dashboard
    fetchActiveErrors(1, 20)
      .then(data => setErrors(data.errors))
      .catch(console.error);

    fetchStats()
      .then(setStats)
      .catch(console.error);

    return () => ws.disconnect();
  }, [handleMessage]);

  // Clear "new" status after animation
  useEffect(() => {
    if (newErrorIds.size > 0) {
      const timer = setTimeout(() => setNewErrorIds(new Set()), 3000);
      return () => clearTimeout(timer);
    }
  }, [newErrorIds]);

  return (
    <BrowserRouter>
      <Header isConnected={isConnected} />
      <Routes>
        <Route path="/" element={
          <Dashboard
            errors={errors}
            stats={stats}
            newErrorIds={newErrorIds}
            onDismiss={handleDismiss}
            onDismissAll={handleDismissAll}
          />
        } />
        <Route path="/history" element={<History />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
