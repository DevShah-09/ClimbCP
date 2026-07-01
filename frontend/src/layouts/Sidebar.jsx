import { NavLink } from 'react-router-dom';
import { LayoutDashboard, BookOpen, AlertTriangle, Lightbulb, TrendingUp, Sparkles, Compass, Users } from 'lucide-react';
import { useAnalytics } from '../hooks/AnalyticsContext';

const navItems = [
  { to: '/',              icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/topics',        icon: BookOpen,         label: 'Topic Analytics' },
  { to: '/weaknesses',    icon: AlertTriangle,    label: 'Weakness Analysis' },
  { to: '/recommendations', icon: Lightbulb,      label: 'Recommendations' },
  { to: '/ai-coach',      icon: Sparkles,         label: 'AI Coach' },
  { to: '/similar-users', icon: Users,            label: 'Similar Users' },
];

export default function Sidebar() {
  const { handle, analytics, clearData } = useAnalytics();

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-56 border-r border-border bg-surface/90 backdrop-blur-md flex flex-col z-30">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 h-16 border-b border-border shrink-0">
        <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center">
          <TrendingUp size={14} className="text-white" />
        </div>
        <span className="font-kalam font-bold text-lg text-white tracking-wide">ClimbCP</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'active' : ''}`
            }
          >
            <Icon size={16} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User info at bottom */}
      {handle && analytics && (
        <div className="p-3 border-t border-border space-y-2">
          <div className="glass-card p-3 space-y-1">
            <p className="text-xs text-text-muted">Viewing</p>
            <p className="font-mono font-semibold text-sm text-accent truncate">{handle}</p>
            {analytics.current_rating && (
              <p className="text-xs text-text-muted">
                Rating: <span className="text-text-secondary">{analytics.current_rating}</span>
              </p>
            )}
          </div>
          <button
            onClick={clearData}
            className="w-full py-1.5 px-3 rounded-lg bg-muted hover:bg-red-500/10 hover:text-red-400 border border-border text-xs text-text-secondary transition-all cursor-pointer font-medium text-center"
          >
            Switch Profile / Log Out
          </button>
        </div>
      )}


    </aside>
  );
}
