import { User } from 'lucide-react';
import { useAnalytics } from '../hooks/AnalyticsContext';

export default function TopNavbar() {
  const { handle, analytics } = useAnalytics();

  const ratingColor = (r) => {
    if (!r) return 'text-text-muted';
    if (r >= 2400) return 'text-red-400';
    if (r >= 2100) return 'text-amber-400';
    if (r >= 1900) return 'text-violet-400';
    if (r >= 1600) return 'text-blue-400';
    if (r >= 1400) return 'text-teal-400';
    return 'text-text-secondary';
  };

  return (
    <header className="fixed top-0 right-0 left-56 h-16 border-b border-border bg-surface/90 backdrop-blur-md flex items-center px-6 gap-4 z-20">
      {/* User profile area */}
      {analytics && handle ? (
        <div className="flex items-center gap-3 glass-card px-3 py-1.5">
          <div className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center">
            <User size={14} className="text-accent" />
          </div>
          <div className="text-xs">
            <p className="font-semibold text-text-primary">{handle}</p>
            {analytics.current_rating && (
              <p className={`font-mono font-bold ${ratingColor(analytics.current_rating)}`}>
                {analytics.current_rating}
              </p>
            )}
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <div className="w-7 h-7 rounded-full bg-muted border border-border flex items-center justify-center">
            <User size={14} />
          </div>
          <span>No handle</span>
        </div>
      )}
    </header>
  );
}
