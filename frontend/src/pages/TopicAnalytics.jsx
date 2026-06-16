import { useAnalytics } from '../hooks/AnalyticsContext';
import RadarChart from '../components/RadarChart';
import TopicTable from '../components/TopicTable';
import { LoadingSpinner, ErrorState, NotSearchedState } from '../components/UIStates';

export default function TopicAnalytics() {
  const { handle, topicData, loading, error } = useAnalytics();

  if (!handle && !loading) return <NotSearchedState />;
  if (loading) return <LoadingSpinner message="Loading topic analytics…" />;
  if (error) return <ErrorState message={error} />;

  const data = Array.isArray(topicData) ? topicData : [];

  const avgScore = data.length
    ? Math.round(data.reduce((a, d) => a + (d.score ?? 0), 0) / data.length)
    : null;

  const strongest = data.length
    ? [...data].sort((a, b) => (b.score ?? 0) - (a.score ?? 0))[0]
    : null;

  const weakest = data.length
    ? [...data].sort((a, b) => (a.score ?? 0) - (b.score ?? 0))[0]
    : null;

  return (
    <div className="space-y-6 animate-fade-in pb-8">
      <div>
        <p className="text-text-muted text-sm mb-1">Topic Analytics</p>
        <h1 className="font-kalam font-bold text-3xl text-white">Topic Mastery</h1>
      </div>

      {/* Quick stats */}
      {data.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <div className="glass-card p-4 text-center">
            <p className="stat-label mb-1">Avg Score</p>
            <p className="text-3xl font-bold text-accent">{avgScore}</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="stat-label mb-1">Strongest</p>
            <p className="text-lg font-bold text-emerald-400 truncate">{strongest?.topic}</p>
            <p className="text-xs text-text-muted font-mono">{strongest?.score}/100</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="stat-label mb-1">Weakest</p>
            <p className="text-lg font-bold text-red-400 truncate">{weakest?.topic}</p>
            <p className="text-xs text-text-muted font-mono">{weakest?.score}/100</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RadarChart data={data} />
        <div className="flex flex-col justify-center gap-4">
          {data.length === 0 ? (
            <div className="glass-card p-6 text-center text-text-muted text-sm">
              No topic data available. This requires Phase 2 backend features.
              <p className="mt-2 text-xs text-accent">Mock data shown below.</p>
            </div>
          ) : null}
          <div className="glass-card p-5 space-y-3">
            <h3 className="section-title">Score Legend</h3>
            {[
              { range: '80–100', label: 'Expert', color: 'text-accent' },
              { range: '65–79',  label: 'Strong',   color: 'text-emerald-400' },
              { range: '50–64',  label: 'Moderate', color: 'text-amber-400' },
              { range: '0–49',   label: 'Weak',     color: 'text-red-400' },
            ].map(({ range, label, color }) => (
              <div key={label} className="flex items-center justify-between text-sm">
                <span className="font-mono text-text-muted text-xs">{range}</span>
                <span className={`font-semibold ${color}`}>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <TopicTable data={data} />
    </div>
  );
}
