import { ExternalLink, Zap, TrendingUp } from 'lucide-react';

// Maps the backend difficulty_tier to visual badge styles
const tierConfig = {
  'Easy Stretch':  { badge: 'badge-success', dot: 'bg-emerald-400', label: 'Easy Stretch'  },
  'Current Level': { badge: 'badge-warning', dot: 'bg-amber-400',   label: 'Current Level' },
  'Challenge':     { badge: 'badge-danger',  dot: 'bg-red-400',     label: 'Challenge'      },
};

export default function RecommendationCard({
  name,
  problem_code,
  rating,
  topics = [],
  difficulty_tier,
  priority_score,
  reason,
}) {
  const cfg = tierConfig[difficulty_tier] || tierConfig['Current Level'];
  const cfUrl = problem_code
    ? (() => {
        const match = problem_code.match(/^(\d+)([A-Z]\d*)$/);
        return match
          ? `https://codeforces.com/problemset/problem/${match[1]}/${match[2]}`
          : 'https://codeforces.com/problemset';
      })()
    : 'https://codeforces.com/problemset';

  return (
    <div className="glass-card-hover p-5 flex flex-col gap-3 animate-slide-up group">
      <div className="flex items-start justify-between gap-3">
        <h4 className="font-semibold text-text-primary leading-snug group-hover:text-white transition-colors">
          {name}
        </h4>
        <a
          href={cfUrl}
          target="_blank"
          rel="noopener noreferrer"
          onClick={e => e.stopPropagation()}
          title="Open on Codeforces"
        >
          <ExternalLink size={14} className="text-text-muted group-hover:text-accent transition-colors shrink-0 mt-0.5" />
        </a>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <span className={`badge ${cfg.badge}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
          {cfg.label}
        </span>
        {rating != null && (
          <span className="badge bg-muted text-text-secondary border border-border font-mono">
            ★ {rating}
          </span>
        )}
        {priority_score != null && (
          <span className="badge bg-muted text-text-secondary border border-border text-xs flex items-center gap-1">
            <TrendingUp size={10} />
            {priority_score}
          </span>
        )}
        {topics.map((t, i) => (
          <span key={i} className="badge bg-accent/8 text-accent-purple border border-accent-purple/20 text-xs">
            {t}
          </span>
        ))}
      </div>

      {reason && (
        <div className="flex items-start gap-2 pt-1 border-t border-border/50">
          <Zap size={12} className="text-accent mt-0.5 shrink-0" />
          <p className="text-xs text-text-secondary leading-relaxed">{reason}</p>
        </div>
      )}
    </div>
  );
}
