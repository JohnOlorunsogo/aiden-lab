import { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { fetchErrors, fetchStats, fetchHealth, WebSocketManager } from './services/api';

// ===== Components =====

function Header({ isConnected }) {
  return (
    <header className="header">
      <div className="container header-content">
        <div className="logo">
          <div className="logo-icon">🔍</div>
          <span>AIDEN Labs</span>
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
        <div className="stat-value">{stats.total_errors || 0}</div>
        <div className="stat-label">Total Errors</div>
      </div>
      <div className="card stat-card">
        <div className="stat-value">{stats.devices_count || 0}</div>
        <div className="stat-label">Devices Monitored</div>
      </div>
      <div className="card stat-card">
        <div className="stat-value">{stats.watched_files?.length || 0}</div>
        <div className="stat-label">Active Log Files</div>
      </div>
      <div className="card stat-card">
        <div className="stat-value" style={{ color: stats.watcher_running ? 'var(--color-success)' : 'var(--color-error)' }}>
          {stats.watcher_running ? '●' : '○'}
        </div>
        <div className="stat-label">Watcher {stats.watcher_running ? 'Active' : 'Inactive'}</div>
      </div>
    </div>
  );
}

function ErrorCard({ error, solution, isNew }) {
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
        <div className="error-meta">
          <span>{new Date(error.timestamp).toLocaleString()}</span>
        </div>
      </div>

      <div className="error-line">{error.error_line}</div>

      {solution && (
        <div className="solution">
          <div className="solution-section">
            <div className="solution-label">Root Cause</div>
            <div className="solution-content">{solution.root_cause}</div>
          </div>
          <div className="solution-section">
            <div className="solution-label">Solution</div>
            <div className="solution-content">{solution.solution}</div>
          </div>
          {expanded && (
            <>
              <div className="solution-section">
                <div className="solution-label">Impact</div>
                <div className="solution-content">{solution.impact}</div>
              </div>
              <div className="solution-section">
                <div className="solution-label">Prevention</div>
                <div className="solution-content">{solution.prevention}</div>
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

function ErrorList({ errors, newErrorIds }) {
  if (errors.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📋</div>
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
        />
      ))}
    </div>
  );
}

function Dashboard({ errors, stats, newErrorIds }) {
  return (
    <div className="page">
      <div className="container">
        <h1 style={{ marginBottom: 'var(--space-lg)' }}>Dashboard</h1>
        <StatsGrid stats={stats} />
        <h2 style={{ marginBottom: 'var(--space-md)' }}>Recent Errors</h2>
        <ErrorList errors={errors} newErrorIds={newErrorIds} />
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
        <h1 style={{ marginBottom: 'var(--space-lg)' }}>Error History</h1>
        <ErrorList errors={errors} newErrorIds={new Set()} />
        <div style={{ marginTop: 'var(--space-lg)', display: 'flex', gap: 'var(--space-md)', justifyContent: 'center' }}>
          <button className="btn btn-ghost" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
            Previous
          </button>
          <span style={{ padding: 'var(--space-sm)' }}>Page {page}</span>
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
        <h1 style={{ marginBottom: 'var(--space-lg)' }}>Settings</h1>

        <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
          <h3 style={{ marginBottom: 'var(--space-md)' }}>System Status</h3>
          {health ? (
            <div>
              <p><strong>Status:</strong> {health.status}</p>
              <p><strong>Watcher:</strong> {health.watcher_running ? 'Running' : 'Stopped'}</p>
              <p><strong>Watch Directory:</strong> <code>{health.watch_directory}</code></p>
            </div>
          ) : (
            <p>Loading...</p>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-md)' }}>Configuration</h3>
          <p style={{ color: 'var(--color-text-muted)' }}>
            Configuration is managed via environment variables. Edit the <code>.env</code> file to change settings.
          </p>
          <ul style={{ marginTop: 'var(--space-md)', paddingLeft: 'var(--space-lg)' }}>
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

    // Fetch initial data
    fetchErrors(1, 20)
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
        <Route path="/" element={<Dashboard errors={errors} stats={stats} newErrorIds={newErrorIds} />} />
        <Route path="/history" element={<History />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
