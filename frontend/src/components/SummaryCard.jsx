import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function SummaryCard({ icon: Icon, label, value, sub, trend, accentColor = 'accent', loading = false }) {
  if (loading) {
    return (
      <div className="glass-card p-5 flex flex-col gap-3">
        <div className="skeleton h-4 w-20 rounded" />
        <div className="skeleton h-9 w-32 rounded" />
        <div className="skeleton h-3 w-24 rounded" />
      </div>
    );
  }

  const trendIcon = trend > 0 ? TrendingUp : trend < 0 ? TrendingDown : Minus;
  const trendColor = trend > 0 ? 'text-emerald-400' : trend < 0 ? 'text-red-400' : 'text-text-muted';
  const TrendIcon = trendIcon;

  const accentMap = {
    accent: 'bg-accent/10 text-accent',
    pink: 'bg-accent-pink/10 text-accent-pink',
    purple: 'bg-accent-purple/10 text-accent-purple',
    emerald: 'bg-emerald-500/10 text-emerald-400',
    amber: 'bg-amber-500/10 text-amber-400',
  };

  return (
    <div className="glass-card-hover p-5 flex flex-col gap-3 animate-slide-up">
      <div className="flex items-center justify-between">
        <span className="stat-label">{label}</span>
        {Icon && (
          <div className={`p-2 rounded-lg ${accentMap[accentColor] || accentMap.accent}`}>
            <Icon size={16} />
          </div>
        )}
      </div>
      <div className="stat-value">{value ?? '—'}</div>
      {(sub || trend !== undefined) && (
        <div className="flex items-center gap-1.5 text-xs text-text-muted">
          {trend !== undefined && <TrendIcon size={12} className={trendColor} />}
          {sub && <span>{sub}</span>}
        </div>
      )}
    </div>
  );
}
