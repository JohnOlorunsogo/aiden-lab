import { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { fetchErrors, fetchActiveErrors, fetchStats, fetchHealth, dismissError, dismissAllErrors, WebSocketManager } from './services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LayoutDashboard, 
  History, 
  Settings, 
  Clipboard, 
  AlertTriangle, 
  Monitor, 
  FileText, 
  Activity, 
  X, 
  CheckCircle,
  Terminal,
  Server,
  Cpu,
  Wifi,
  Database,
  Menu,
  ChevronLeft,
  Sparkles,
  Shield
} from 'lucide-react';
import AdminLayout from './pages/admin/AdminLayout';
import AdminDashboard from './pages/admin/AdminDashboard';
import CreateVMPage from './pages/admin/CreateVMPage';
import VMDetailsPage from './pages/admin/VMDetailsPage';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { StatsCard } from '@/components/ui/stats-card';
import { Skeleton } from '@/components/ui/skeleton';
import { Toaster } from 'sonner';
import { cn } from '@/lib/utils';

// ===== Utility Components =====

function FormattedContent({ text }) {
  if (!text) return null;

  const formatText = (content) => {
    const parts = [];
    let key = 0;

    const codeBlockRegex = /```(\w*)\n?([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        const beforeText = content.slice(lastIndex, match.index);
        parts.push(...formatInlineText(beforeText, key));
        key += 100;
      }

      const language = match[1] || 'code';
      const code = match[2].trim();
      parts.push(
        <div key={`code-${key++}`} className="code-block">
          <div className="code-header">{language.toUpperCase()}</div>
          <code>{code}</code>
        </div>
      );

      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < content.length) {
      parts.push(...formatInlineText(content.slice(lastIndex), key));
    }

    return parts;
  };

  const formatInlineText = (text, startKey = 0) => {
    let key = startKey;
    const lines = text.split('\n');
    const elements = [];

    lines.forEach((line, index) => {
      const trimmedLine = line.trim();

      if (!trimmedLine) {
        if (index > 0) {
          elements.push(<br key={`br-${key++}`} />);
        }
        return;
      }

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

      if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ')) {
        elements.push(
          <div key={`bullet-${key++}`} className="list-item">
            <span className="list-bullet">-</span>
            <span>{formatBoldText(trimmedLine.slice(2))}</span>
          </div>
        );
        return;
      }

      elements.push(
        <p key={`p-${key++}`} style={{ margin: '0.25rem 0' }}>
          {formatBoldText(trimmedLine)}
        </p>
      );
    });

    return elements;
  };

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

function MobileNav({ isOpen, onClose, isConnected }) {
  const location = useLocation();
  
  useEffect(() => {
    onClose();
  }, [location.pathname, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
          />
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed top-0 left-0 bottom-0 w-[280px] bg-[#020725]/95 backdrop-blur-xl border-r border-[#bdccd4]/10 z-50 md:hidden"
          >
            <div className="flex flex-col h-full p-6">
              <div className="flex items-center justify-between mb-8">
                <img 
                  src="/Aiden lab Assets (Png & SVG)/White/Asset 9.svg" 
                  alt="AIDEN Labs" 
                  className="h-6 w-auto"
                />
                <Button variant="ghost" size="icon" onClick={onClose} className="text-[#bdccd4]/60">
                  <ChevronLeft className="w-5 h-5" />
                </Button>
              </div>

              <nav className="flex flex-col gap-1 flex-1">
                <NavLink to="/" className={({ isActive }) => cn(
                  'flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200',
                  isActive 
                    ? 'bg-[#24ab94]/10 text-[#24ab94]' 
                    : 'text-[#bdccd4]/60 hover:bg-[#bdccd4]/5 hover:text-[#bdccd4]'
                )}>
                  <LayoutDashboard className="w-5 h-5" />
                  <span>Dashboard</span>
                </NavLink>
                <NavLink to="/history" className={({ isActive }) => cn(
                  'flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200',
                  isActive 
                    ? 'bg-[#24ab94]/10 text-[#24ab94]' 
                    : 'text-[#bdccd4]/60 hover:bg-[#bdccd4]/5 hover:text-[#bdccd4]'
                )}>
                  <History className="w-5 h-5" />
                  <span>History</span>
                </NavLink>
                <NavLink to="/admin" className={({ isActive }) => cn(
                  'flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200',
                  isActive 
                    ? 'bg-[#24ab94]/10 text-[#24ab94]' 
                    : 'text-[#bdccd4]/60 hover:bg-[#bdccd4]/5 hover:text-[#bdccd4]'
                )}>
                  <Server className="w-5 h-5" />
                  <span>VM Admin</span>
                </NavLink>
                <NavLink to="/settings" className={({ isActive }) => cn(
                  'flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200',
                  isActive 
                    ? 'bg-[#24ab94]/10 text-[#24ab94]' 
                    : 'text-[#bdccd4]/60 hover:bg-[#bdccd4]/5 hover:text-[#bdccd4]'
                )}>
                  <Settings className="w-5 h-5" />
                  <span>Settings</span>
                </NavLink>
              </nav>

              <div className="pt-4 border-t border-[#bdccd4]/10">
                <div className="flex items-center gap-3 px-4 py-3 bg-[#010311]/50 rounded-lg border border-[#bdccd4]/5">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${isConnected ? 'bg-[#24ab94] shadow-[0_0_10px_rgba(36,171,148,0.6)]' : 'bg-red-500'}`} />
                  <span className="text-xs text-[#bdccd4]/70">{isConnected ? 'System Online' : 'Disconnected'}</span>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function Sidebar({ isConnected }) {
  return (
    <aside className="fixed top-0 left-0 bottom-0 w-[280px] border-r border-[#bdccd4]/10 flex-col z-50 hidden md:flex">
      <div className="sidebar-pattern opacity-[0.03]" />
      <div className="absolute inset-0 bg-[#020725]/80 backdrop-blur-xl" />
      
      <div className="relative z-10 flex flex-col h-full">
        <div className="flex items-center gap-3 mb-10 px-6 pt-6">
          <img 
            src="/Aiden lab Assets (Png & SVG)/White/Asset 9.svg" 
            alt="AIDEN Labs" 
            className="h-6 w-auto"
          />
        </div>

        <div className="px-6 mb-8">
          <p className="text-[10px] text-[#24ab94]/60 uppercase tracking-[0.25em] font-medium">
            AI-Driven Elastic Network Laboratory
          </p>
        </div>

        <nav className="flex flex-col gap-1 flex-1 px-3">
          <NavLink to="/" className={({ isActive }) => cn(
            'flex items-center gap-3 px-4 py-3 text-[13px] font-medium rounded-lg transition-all duration-200 group relative',
            isActive 
              ? 'text-[#24ab94]' 
              : 'text-[#bdccd4]/60 hover:text-[#bdccd4]'
          )}>
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active-main"
                    className="absolute inset-0 bg-[#24ab94]/10 rounded-lg"
                    transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <LayoutDashboard className={cn('w-4 h-4 relative z-10', !isActive && 'group-hover:scale-110 transition-transform')} />
                <span className="relative z-10">Dashboard</span>
              </>
            )}
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => cn(
            'flex items-center gap-3 px-4 py-3 text-[13px] font-medium rounded-lg transition-all duration-200 group relative',
            isActive 
              ? 'text-[#24ab94]' 
              : 'text-[#bdccd4]/60 hover:text-[#bdccd4]'
          )}>
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active-main"
                    className="absolute inset-0 bg-[#24ab94]/10 rounded-lg"
                    transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <History className={cn('w-4 h-4 relative z-10', !isActive && 'group-hover:scale-110 transition-transform')} />
                <span className="relative z-10">History</span>
              </>
            )}
          </NavLink>
          <NavLink to="/admin" className={({ isActive }) => cn(
            'flex items-center gap-3 px-4 py-3 text-[13px] font-medium rounded-lg transition-all duration-200 group relative',
            isActive 
              ? 'text-[#24ab94]' 
              : 'text-[#bdccd4]/60 hover:text-[#bdccd4]'
          )}>
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active-main"
                    className="absolute inset-0 bg-[#24ab94]/10 rounded-lg"
                    transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <Server className={cn('w-4 h-4 relative z-10', !isActive && 'group-hover:scale-110 transition-transform')} />
                <span className="relative z-10">VM Admin</span>
              </>
            )}
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => cn(
            'flex items-center gap-3 px-4 py-3 text-[13px] font-medium rounded-lg transition-all duration-200 group relative',
            isActive 
              ? 'text-[#24ab94]' 
              : 'text-[#bdccd4]/60 hover:text-[#bdccd4]'
          )}>
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active-main"
                    className="absolute inset-0 bg-[#24ab94]/10 rounded-lg"
                    transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <Settings className={cn('w-4 h-4 relative z-10', !isActive && 'group-hover:scale-110 transition-transform')} />
                <span className="relative z-10">Settings</span>
              </>
            )}
          </NavLink>
        </nav>

        <div className="pt-4 px-6 border-t border-[#bdccd4]/10">
          <div className="flex items-center gap-3 px-4 py-3 bg-[#010311]/50 rounded-lg border border-[#bdccd4]/5">
            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${isConnected ? 'bg-[#24ab94] shadow-[0_0_10px_rgba(36,171,148,0.6)]' : 'bg-red-500'}`} />
            <span className="text-xs text-[#bdccd4]/70">{isConnected ? 'System Online' : 'Disconnected'}</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

function StatsGrid({ stats }) {
  const statsData = [
    { 
      label: 'Total Errors', 
      value: stats.total_errors || 0, 
      icon: AlertTriangle, 
      color: 'red',
      trend: stats.total_errors > 0 ? -5 : 0,
      trendUp: false
    },
    { 
      label: 'Devices Monitored', 
      value: stats.devices_count || 0, 
      icon: Monitor, 
      color: 'blue',
      trend: 12,
      trendUp: true
    },
    { 
      label: 'Active Log Files', 
      value: stats.watched_files?.length || 0, 
      icon: FileText, 
      color: 'amber',
      trend: 8,
      trendUp: true
    },
    { 
      label: 'Watcher Status', 
      value: stats.watcher_running ? 'Active' : 'Inactive', 
      icon: Activity, 
      color: stats.watcher_running ? 'teal' : 'red',
      isStatus: true
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {statsData.map((stat, i) => (
        <StatsCard
          key={stat.label}
          title={stat.label}
          value={stat.value}
          icon={stat.icon}
          trend={stat.trend}
          trendUp={stat.trendUp}
          color={stat.color}
          delay={i * 0.1}
        />
      ))}
    </div>
  );
}

function ErrorCard({ error, solution, isNew, onDismiss, showDismiss = true }) {
  const [expanded, setExpanded] = useState(false);

  const severityConfig = {
    critical: { 
      border: 'border-l-red-500', 
      badge: 'destructive',
      bg: 'from-red-500/5 to-transparent'
    },
    warning: { 
      border: 'border-l-amber-500', 
      badge: 'warning',
      bg: 'from-amber-500/5 to-transparent'
    },
    info: { 
      border: 'border-l-[#24ab94]', 
      badge: 'secondary',
      bg: 'from-[#24ab94]/5 to-transparent'
    }
  };

  const config = severityConfig[error.severity] || severityConfig.info;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'relative overflow-hidden rounded-xl border border-[#bdccd4]/10',
        'bg-gradient-to-br from-[#020725]/60 to-transparent',
        'backdrop-blur-sm transition-all duration-300',
        'hover:border-[#bdccd4]/20',
        config.border,
        'border-l-4',
        isNew && 'ring-2 ring-[#24ab94]/20'
      )}
    >
      <div className={cn('absolute inset-0 bg-gradient-to-br opacity-30', config.bg)} />
      
      <div className="relative p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3 flex-wrap">
            <Badge variant={config.badge} className="text-[10px] uppercase tracking-wider font-bold">
              {error.severity}
            </Badge>
            <span className="text-xs text-[#bdccd4]/50 font-mono">{error.device_id}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] text-[#bdccd4]/40 font-mono hidden sm:inline">
              {new Date(error.timestamp).toLocaleString()}
            </span>
            {showDismiss && onDismiss && (
              <Button 
                variant="ghost" 
                size="icon" 
                className="h-8 w-8 text-[#bdccd4]/40 hover:text-red-400 hover:bg-red-500/10" 
                onClick={() => onDismiss(error.id)}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        <div className="font-mono text-sm text-red-300 bg-red-950/30 p-4 rounded-lg border border-red-900/30 my-3 overflow-x-auto">
          {error.error_line}
        </div>

        {solution && (
          <div className="mt-6 pt-6 border-t border-[#bdccd4]/10">
            <div className="mb-5">
              <div className="flex items-center gap-2 text-[10px] font-bold text-[#24ab94] mb-3 uppercase tracking-[0.2em]">
                <Sparkles className="w-3 h-3" />
                Root Cause
                <div className="h-px flex-1 bg-[#24ab94]/20" />
              </div>
              <div className="text-[13px] text-[#bdccd4]/90 whitespace-pre-wrap leading-relaxed">
                <FormattedContent text={solution.root_cause} />
              </div>
            </div>
            <div className="mb-5">
              <div className="flex items-center gap-2 text-[10px] font-bold text-[#24ab94] mb-3 uppercase tracking-[0.2em]">
                <Shield className="w-3 h-3" />
                Solution
                <div className="h-px flex-1 bg-[#24ab94]/20" />
              </div>
              <div className="text-[13px] text-[#bdccd4]/90 whitespace-pre-wrap leading-relaxed">
                <FormattedContent text={solution.solution} />
              </div>
            </div>
            <AnimatePresence>
              {expanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                >
                  <div className="mb-5">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-[#24ab94] mb-3 uppercase tracking-[0.2em]">
                      <Activity className="w-3 h-3" />
                      Impact
                      <div className="h-px flex-1 bg-[#24ab94]/20" />
                    </div>
                    <div className="text-[13px] text-[#bdccd4]/90 whitespace-pre-wrap leading-relaxed">
                      <FormattedContent text={solution.impact} />
                    </div>
                  </div>
                  <div className="mb-5">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-[#24ab94] mb-3 uppercase tracking-[0.2em]">
                      <Database className="w-3 h-3" />
                      Prevention
                      <div className="h-px flex-1 bg-[#24ab94]/20" />
                    </div>
                    <div className="text-[13px] text-[#bdccd4]/90 whitespace-pre-wrap leading-relaxed">
                      <FormattedContent text={solution.prevention} />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setExpanded(!expanded)}
              className="text-[#24ab94] hover:text-[#24ab94] hover:bg-[#24ab94]/10 text-xs uppercase tracking-wider"
            >
              {expanded ? 'Show Less' : 'Show More'}
            </Button>
          </div>
        )}

        {!solution && (
          <div className="mt-6 pt-6 border-t border-[#bdccd4]/10">
            <div className="flex items-center justify-center py-8">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 border-2 border-[#bdccd4]/10 border-t-[#24ab94] rounded-full animate-spin" />
                <span className="text-sm text-[#bdccd4]/60">Analyzing with AI...</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}

function ErrorList({ errors, newErrorIds, onDismiss, showDismiss = true }) {
  if (errors.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center py-20"
      >
        <div className="w-20 h-20 mx-auto mb-6 flex items-center justify-center bg-[#24ab94]/10 rounded-2xl border border-[#24ab94]/20">
          <Clipboard className="w-8 h-8 text-[#24ab94]" />
        </div>
        <h3 className="text-[#bdccd4] font-medium mb-2">No Errors Detected</h3>
        <p className="text-[#bdccd4]/40 text-sm max-w-md mx-auto">
          The system is monitoring your log files. Errors will appear here when detected.
        </p>
      </motion.div>
    );
  }

  return (
    <div className="space-y-4">
      {errors.map((item, index) => (
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
    <div>
      <div className="relative -mx-4 md:-mx-8 -mt-4 md:-mt-8 mb-8 px-4 md:px-8 pt-6 md:pt-8 pb-10 overflow-hidden">
        <div 
          className="absolute inset-0 bg-[#020725]"
          style={{
            backgroundImage: `url('/Aiden lab Assets (Png & SVG)/Patterns/Asset 18.svg')`,
            backgroundSize: '600px',
            backgroundPosition: 'center',
            opacity: 0.15
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#020725]/50 to-[#020725]" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#24ab94]/5 via-transparent to-[#24ab94]/5" />
        
        <div className="relative z-10">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h1 className="text-2xl md:text-3xl font-bold text-[#bdccd4] mb-2 font-notch">Dashboard</h1>
            <p className="text-[#bdccd4]/50 text-sm">Build Better Networks. Guided by AI.</p>
          </motion.div>
          
          {errors.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mt-6"
            >
              <Button 
                variant="ghost" 
                onClick={onDismissAll}
                className="text-[#bdccd4]/60 hover:text-red-400 hover:bg-red-500/10 border border-[#bdccd4]/10"
              >
                <X className="w-4 h-4 mr-2" />
                Clear All Errors
              </Button>
            </motion.div>
          )}
        </div>
      </div>

      <StatsGrid stats={stats} />
      
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="mb-6 text-xs uppercase tracking-[0.2em] text-[#bdccd4]/40 font-medium flex items-center gap-2">
          <Activity className="w-4 h-4" />
          Recent Errors
        </h2>
        <ErrorList errors={errors} newErrorIds={newErrorIds} onDismiss={onDismiss} showDismiss={true} />
      </motion.div>
    </div>
  );
}

function HistoryPage() {
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
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-32 bg-[#020725]/30 rounded-xl border border-[#bdccd4]/10 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="relative -mx-4 md:-mx-8 -mt-4 md:-mt-8 mb-8 px-4 md:px-8 pt-6 md:pt-8 pb-10 overflow-hidden">
        <div 
          className="absolute inset-0 bg-[#020725]"
          style={{
            backgroundImage: `url('/Aiden lab Assets (Png & SVG)/Patterns/Asset 18.svg')`,
            backgroundSize: '600px',
            backgroundPosition: 'center',
            opacity: 0.15
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#020725]/50 to-[#020725]" />
        
        <div className="relative z-10">
          <motion.h1 
            className="text-2xl md:text-3xl font-bold text-[#bdccd4] mb-2 font-notch"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            Error History
          </motion.h1>
          <motion.p 
            className="text-[#bdccd4]/50 text-sm"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            All errors including dismissed ones are shown here.
          </motion.p>
        </div>
      </div>

      <ErrorList errors={errors} newErrorIds={new Set()} showDismiss={false} />
      
      <motion.div 
        className="mt-8 flex gap-4 justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <Button 
          variant="ghost" 
          onClick={() => setPage(p => Math.max(1, p - 1))} 
          disabled={page === 1}
          className="text-[#bdccd4]/60 hover:text-[#24ab94] hover:bg-[#24ab94]/10"
        >
          Previous
        </Button>
        <span className="py-2 px-3 text-[#bdccd4]/40 text-sm font-mono">Page {page}</span>
        <Button 
          variant="ghost" 
          onClick={() => setPage(p => p + 1)}
          className="text-[#bdccd4]/60 hover:text-[#24ab94] hover:bg-[#24ab94]/10"
        >
          Next
        </Button>
      </motion.div>
    </div>
  );
}

function SettingsPage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHealth()
      .then(data => {
        setHealth(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div>
      <div className="relative -mx-4 md:-mx-8 -mt-4 md:-mt-8 mb-8 px-4 md:px-8 pt-6 md:pt-8 pb-10 overflow-hidden">
        <div 
          className="absolute inset-0 bg-[#020725]"
          style={{
            backgroundImage: `url('/Aiden lab Assets (Png & SVG)/Patterns/Asset 18.svg')`,
            backgroundSize: '600px',
            backgroundPosition: 'center',
            opacity: 0.15
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#020725]/50 to-[#020725]" />
        
        <div className="relative z-10">
          <motion.h1 
            className="text-2xl md:text-3xl font-bold text-[#bdccd4] mb-2 font-notch"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            Settings
          </motion.h1>
          <motion.p 
            className="text-[#bdccd4]/50 text-sm"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            Configure your AIDEN Lab environment.
          </motion.p>
        </div>
      </div>

      <div className="grid gap-6 max-w-3xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-[#020725]/40 border-[#bdccd4]/10 backdrop-blur-sm overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#24ab94]/30 to-transparent" />
            <CardHeader>
              <CardTitle className="text-sm uppercase tracking-wider text-[#24ab94] font-bold flex items-center gap-2">
                <Activity className="w-4 h-4" />
                System Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : health ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between py-3 border-b border-[#bdccd4]/5">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-[#24ab94]/10 flex items-center justify-center">
                        <Shield className="w-4 h-4 text-[#24ab94]" />
                      </div>
                      <span className="text-[#bdccd4]/60 text-sm">Status</span>
                    </div>
                    <Badge className="bg-[#24ab94]/10 text-[#24ab94] border-[#24ab94]/30">
                      {health.status}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between py-3 border-b border-[#bdccd4]/5">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-[#24ab94]/10 flex items-center justify-center">
                        <Activity className="w-4 h-4 text-[#24ab94]" />
                      </div>
                      <span className="text-[#bdccd4]/60 text-sm">Watcher</span>
                    </div>
                    <Badge className={health.watcher_running ? 'bg-[#24ab94]/10 text-[#24ab94] border-[#24ab94]/30' : 'bg-red-500/10 text-red-400 border-red-500/30'}>
                      {health.watcher_running ? 'Running' : 'Stopped'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-[#24ab94]/10 flex items-center justify-center">
                        <Terminal className="w-4 h-4 text-[#24ab94]" />
                      </div>
                      <span className="text-[#bdccd4]/60 text-sm">Watch Directory</span>
                    </div>
                    <code className="text-[#24ab94]/80 text-xs bg-[#24ab94]/5 px-3 py-1.5 rounded-lg font-mono">
                      {health.watch_directory}
                    </code>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-[#bdccd4]/40">
                  Failed to load system status
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="bg-[#020725]/40 border-[#bdccd4]/10 backdrop-blur-sm overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#24ab94]/30 to-transparent" />
            <CardHeader>
              <CardTitle className="text-sm uppercase tracking-wider text-[#24ab94] font-bold flex items-center gap-2">
                <Database className="w-4 h-4" />
                Configuration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-[#bdccd4]/50 text-sm mb-6">
                Configuration is managed via environment variables. Edit the <code className="text-[#24ab94]/80 text-xs bg-[#24ab94]/5 px-2 py-1 rounded">.env</code> file to change settings.
              </p>
              <div className="space-y-3">
                {[
                  { key: 'GEMINI_API_KEY', desc: 'Your Gemini API key' },
                  { key: 'LOG_WATCH_DIR', desc: 'Directory to monitor for log files' },
                  { key: 'CONTEXT_LINES', desc: 'Lines of context for AI analysis' }
                ].map((item) => (
                  <div key={item.key} className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 p-4 bg-[#010311]/50 rounded-lg border border-[#bdccd4]/5">
                    <code className="text-[#24ab94] text-xs font-mono">{item.key}</code>
                    <span className="text-[#bdccd4]/40 text-xs">{item.desc}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}

function Header({ isConnected, onMenuClick }) {
  return (
    <header className="md:hidden flex items-center justify-between p-4 bg-[#020725]/80 backdrop-blur-md border-b border-[#bdccd4]/10 sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <img 
          src="/Aiden lab Assets (Png & SVG)/White/Asset 9.svg" 
          alt="AIDEN Labs" 
          className="h-5 w-auto"
        />
      </div>
      <div className="flex items-center gap-3">
        <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[#24ab94] shadow-[0_0_10px_rgba(36,171,148,0.6)]' : 'bg-red-500'}`} />
        <Button variant="ghost" size="icon" onClick={onMenuClick} className="text-[#bdccd4]/60">
          <Menu className="w-5 h-5" />
        </Button>
      </div>
    </header>
  );
}

// ===== Main App =====

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [errors, setErrors] = useState([]);
  const [stats, setStats] = useState({});
  const [newErrorIds, setNewErrorIds] = useState(new Set());
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const handleDismiss = useCallback(async (errorId) => {
    try {
      await dismissError(errorId);
      setErrors(prev => prev.filter(e => e.error.id !== errorId));
      fetchStats().then(setStats).catch(console.error);
    } catch (err) {
      console.error('Failed to dismiss error:', err);
    }
  }, []);

  const handleDismissAll = useCallback(async () => {
    try {
      await dismissAllErrors();
      setErrors([]);
      fetchStats().then(setStats).catch(console.error);
    } catch (err) {
      console.error('Failed to dismiss all errors:', err);
    }
  }, []);

  const handleMessage = useCallback((data) => {
    if (data.type === 'error_update') {
      setErrors(prev => {
        const existing = prev.findIndex(e => e.error.id === data.data.error.id);
        if (existing >= 0) {
          const updated = [...prev];
          updated[existing] = data.data;
          return updated;
        }
        setNewErrorIds(ids => new Set([...ids, data.data.error.id]));
        return [data.data, ...prev.slice(0, 49)];
      });
      fetchStats().then(setStats).catch(console.error);
    }
  }, []);

  // Synchronize state from REST API
  const syncState = useCallback(async () => {
    try {
      const data = await fetchActiveErrors(1, 20);
      setErrors(prev => {
        const prevIds = new Set(prev.map(item => item.error.id));
        const newlyAddedIds = data.errors
          .filter(item => !prevIds.has(item.error.id))
          .map(item => item.error.id);

        if (newlyAddedIds.length > 0) {
          setNewErrorIds(ids => new Set([...ids, ...newlyAddedIds]));
        }
        return data.errors;
      });

      const statsData = await fetchStats();
      setStats(statsData);
    } catch (err) {
      console.error('Failed to sync state:', err);
    }
  }, []);

  // Interval-based polling when disconnected
  useEffect(() => {
    if (isConnected) return;

    // Fallback polling when WebSocket drops
    const interval = setInterval(() => {
      syncState();
    }, 5000); // 5 seconds interval

    return () => clearInterval(interval);
  }, [isConnected, syncState]);

  // Initialize WebSocket and fetch initial data
  useEffect(() => {
    const ws = new WebSocketManager(
      handleMessage,
      (isReconnect) => {
        setIsConnected(true);
        if (isReconnect) syncState();
      },
      () => setIsConnected(false)
    );
    ws.connect();

    // Fetch initial state once on mount
    // eslint-disable-next-line react-hooks/set-state-in-effect
    syncState();

    return () => ws.disconnect();
  }, [handleMessage, syncState]);

  useEffect(() => {
    if (newErrorIds.size > 0) {
      const timer = setTimeout(() => setNewErrorIds(new Set()), 3000);
      return () => clearTimeout(timer);
    }
  }, [newErrorIds]);

  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-[#010311]">
        <Sidebar isConnected={isConnected} />
        <MobileNav isOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} isConnected={isConnected} />
        
        <div className="flex-1 flex flex-col md:ml-[280px]">
          <Header isConnected={isConnected} onMenuClick={() => setMobileNavOpen(true)} />
          
          <main className="flex-1 p-4 md:p-8 min-h-screen">
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
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/admin" element={<AdminLayout />}>
                <Route index element={<AdminDashboard />} />
                <Route path="vms/new" element={<CreateVMPage />} />
                <Route path="vms/:id" element={<VMDetailsPage />} />
              </Route>
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </main>
        </div>
      </div>
      <Toaster 
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#020725',
            border: '1px solid rgba(189, 204, 212, 0.1)',
            color: '#bdccd4',
          },
        }}
      />
    </BrowserRouter>
  );
}

export default App;
