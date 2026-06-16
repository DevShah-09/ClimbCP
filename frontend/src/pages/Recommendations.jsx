import { useState } from 'react';
import { useAnalytics } from '../hooks/AnalyticsContext';
import RecommendationCard from '../components/RecommendationCard';
import { LoadingSpinner, ErrorState, NotSearchedState, EmptyState } from '../components/UIStates';
import { Lightbulb, Filter } from 'lucide-react';

const ALL = 'All';

export default function Recommendations() {
  const { handle, recommendations, loading, error } = useAnalytics();
  const [filter, setFilter] = useState(ALL);

  if (!handle && !loading) return <NotSearchedState />;
  if (loading) return <LoadingSpinner message="Generating recommendations…" />;
  if (error) return <ErrorState message={error} />;

  const data = Array.isArray(recommendations) ? recommendations : [];
  const difficulties = [ALL, ...new Set(data.map(d => d.difficulty).filter(Boolean))];
  const filtered = filter === ALL ? data : data.filter(d => d.difficulty === filter);

  return (
    <div className="space-y-6 animate-fade-in pb-8">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <p className="text-text-muted text-sm mb-1">Recommendations</p>
          <h1 className="font-kalam font-bold text-3xl text-white">Problem Suggestions</h1>
        </div>
        <div className="glass-card px-3 py-2 text-xs text-text-muted flex items-center gap-1.5">
          <Lightbulb size={12} className="text-accent" />
          AI-powered · Phase 3 feature
        </div>
      </div>

      {/* Filter chips */}
      {data.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <Filter size={13} className="text-text-muted" />
          {difficulties.map(d => (
            <button
              key={d}
              onClick={() => setFilter(d)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-all duration-200 ${
                filter === d
                  ? 'bg-accent text-white border-accent'
                  : 'bg-muted text-text-secondary border-border hover:border-accent/40 hover:text-text-primary'
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      )}

      {/* Stats bar */}
      {data.length > 0 && (
        <div className="glass-card p-4 flex gap-6 text-sm flex-wrap">
          <div>
            <span className="text-text-muted">Total</span>
            <span className="ml-2 font-bold text-text-primary">{filtered.length}</span>
          </div>
          {['Easy', 'Medium', 'Hard', 'Expert'].map(d => {
            const count = data.filter(r => r.difficulty === d).length;
            if (!count) return null;
            return (
              <div key={d}>
                <span className="text-text-muted">{d}</span>
                <span className="ml-2 font-bold text-text-primary">{count}</span>
              </div>
            );
          })}
        </div>
      )}

      {filtered.length === 0 ? (
        <EmptyState icon={Lightbulb} message="No recommendations available yet." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((rec, i) => (
            <RecommendationCard key={i} {...rec} />
          ))}
        </div>
      )}
    </div>
  );
}
