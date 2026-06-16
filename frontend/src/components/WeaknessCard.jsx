import { AlertTriangle, ChevronRight } from 'lucide-react';

const priorityConfig = {
  High:   { badge: 'badge-danger',   bar: 'bg-red-500',   glow: 'rgba(239,68,68,0.08)' },
  Medium: { badge: 'badge-warning',  bar: 'bg-amber-500', glow: 'rgba(245,158,11,0.08)' },
  Low:    { badge: 'badge-success',  bar: 'bg-emerald-500', glow: 'rgba(52,211,153,0.08)' },
};

export default function WeaknessCard({ topic, score, priority, suggestion }) {
  const cfg = priorityConfig[priority] || priorityConfig.Medium;

  return (
    <div
      className="glass-card-hover p-5 flex flex-col gap-4 animate-slide-up"
      style={{ boxShadow: `0 0 0 1px ${cfg.glow}, 0 8px 24px ${cfg.glow}` }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-muted">
            <AlertTriangle size={15} className="text-text-muted" />
          </div>
          <div>
            <h4 className="font-semibold text-text-primary leading-tight">{topic}</h4>
            <p className="text-xs text-text-muted mt-0.5">Weakness Area</p>
          </div>
        </div>
        <span className={`badge ${cfg.badge} shrink-0`}>{priority} Priority</span>
      </div>

      {/* Score bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-text-muted">Mastery Score</span>
          <span className="font-mono font-semibold text-text-primary">{score}/100</span>
        </div>
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${cfg.bar}`}
            style={{ width: `${score}%` }}
          />
        </div>
      </div>

      {/* Suggestion */}
      {suggestion && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-muted/60 border border-border/50">
          <ChevronRight size={14} className="text-accent mt-0.5 shrink-0" />
          <p className="text-xs text-text-secondary leading-relaxed">{suggestion}</p>
        </div>
      )}
    </div>
  );
}
