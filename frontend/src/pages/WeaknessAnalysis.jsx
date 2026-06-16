import { useAnalytics } from '../hooks/AnalyticsContext';
import WeaknessCard from '../components/WeaknessCard';
import { LoadingSpinner, ErrorState, NotSearchedState, EmptyState } from '../components/UIStates';
import { ShieldAlert } from 'lucide-react';

const priorityOrder = { High: 0, Medium: 1, Low: 2 };

export default function WeaknessAnalysis() {
  const { handle, weaknesses, loading, error } = useAnalytics();

  if (!handle && !loading) return <NotSearchedState />;
  if (loading) return <LoadingSpinner message="Analyzing weaknesses…" />;
  if (error) return <ErrorState message={error} />;

  const data = Array.isArray(weaknesses) ? weaknesses : [];
  const sorted = [...data].sort(
    (a, b) => (priorityOrder[a.priority] ?? 2) - (priorityOrder[b.priority] ?? 2)
  );

  const highCount = data.filter(d => d.priority === 'High').length;
  const medCount  = data.filter(d => d.priority === 'Medium').length;
  const lowCount  = data.filter(d => d.priority === 'Low').length;

  return (
    <div className="space-y-6 animate-fade-in pb-8">
      <div>
        <p className="text-text-muted text-sm mb-1">Weakness Analysis</p>
        <h1 className="font-kalam font-bold text-3xl text-white">Areas to Improve</h1>
      </div>

      {/* Priority summary */}
      {data.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <div className="glass-card p-4 text-center border-red-500/20">
            <p className="stat-label mb-1">High Priority</p>
            <p className="text-3xl font-bold text-red-400">{highCount}</p>
          </div>
          <div className="glass-card p-4 text-center border-amber-500/20">
            <p className="stat-label mb-1">Medium Priority</p>
            <p className="text-3xl font-bold text-amber-400">{medCount}</p>
          </div>
          <div className="glass-card p-4 text-center border-emerald-500/20">
            <p className="stat-label mb-1">Low Priority</p>
            <p className="text-3xl font-bold text-emerald-400">{lowCount}</p>
          </div>
        </div>
      )}

      {sorted.length === 0 ? (
        <EmptyState icon={ShieldAlert} message="No weakness data available. Backend Phase 2 features are required." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sorted.map((w, i) => (
            <WeaknessCard key={i} {...w} />
          ))}
        </div>
      )}
    </div>
  );
}
