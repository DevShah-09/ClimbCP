import { ExternalLink, Zap } from 'lucide-react';

const difficultyConfig = {
  Easy:   { badge: 'badge-success', dot: 'bg-emerald-400' },
  Medium: { badge: 'badge-warning', dot: 'bg-amber-400' },
  Hard:   { badge: 'badge-danger',  dot: 'bg-red-400' },
  Expert: { badge: 'badge-accent',  dot: 'bg-accent' },
};

export default function RecommendationCard({ problem_name, rating, topics = [], reason, difficulty }) {
  const cfg = difficultyConfig[difficulty] || difficultyConfig.Medium;

  return (
    <div className="glass-card-hover p-5 flex flex-col gap-3 animate-slide-up group">
      <div className="flex items-start justify-between gap-3">
        <h4 className="font-semibold text-text-primary leading-snug group-hover:text-white transition-colors">
          {problem_name}
        </h4>
        <ExternalLink size={14} className="text-text-muted group-hover:text-accent transition-colors shrink-0 mt-0.5" />
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <span className={`badge ${cfg.badge}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
          {difficulty}
        </span>
        {rating && (
          <span className="badge bg-muted text-text-secondary border border-border font-mono">
            ★ {rating}
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
