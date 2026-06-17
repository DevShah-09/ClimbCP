import { useState, useCallback } from 'react';
import { useAnalytics } from '../hooks/AnalyticsContext';
import RecommendationCard from '../components/RecommendationCard';
import { NotSearchedState, EmptyState } from '../components/UIStates';
import { Lightbulb, Filter, RefreshCw, Loader2, Zap, ChevronRight } from 'lucide-react';
import { analyticsApi } from '../services/api';

const ALL = 'All';
const MAX = 30;
const PRESETS = [5, 10, 15, 20];

// ── Count Picker Screen ────────────────────────────────────────────────────────
function CountPicker({ onSubmit }) {
  const [count, setCount] = useState(10);
  const [inputVal, setInputVal] = useState('10');

  const handlePreset = (n) => {
    setCount(n);
    setInputVal(String(n));
  };

  const handleInput = (e) => {
    const raw = e.target.value.replace(/\D/g, '');
    setInputVal(raw);
    const n = parseInt(raw, 10);
    if (!isNaN(n) && n >= 1 && n <= MAX) setCount(n);
  };

  const valid = count >= 1 && count <= MAX;

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] animate-fade-in">
      {/* Icon glow */}
      <div className="relative mb-8">
        <div className="w-20 h-20 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center">
          <Lightbulb size={36} className="text-accent" />
        </div>
        <div className="absolute inset-0 rounded-2xl bg-accent/5 blur-xl" />
      </div>

      <h1 className="font-kalam font-bold text-3xl text-white mb-2">Problem Suggestions</h1>
      <p className="text-text-muted text-sm mb-10 text-center max-w-xs">
        How many personalised problems would you like to practice today?
      </p>

      {/* Preset chips */}
      <div className="flex items-center gap-3 mb-6">
        {PRESETS.map(n => (
          <button
            key={n}
            onClick={() => handlePreset(n)}
            className={`w-14 h-14 rounded-xl font-bold text-lg border-2 transition-all duration-200 ${
              count === n
                ? 'bg-accent border-accent text-white scale-105 shadow-lg shadow-accent/30'
                : 'bg-muted border-border text-text-secondary hover:border-accent/50 hover:text-text-primary'
            }`}
          >
            {n}
          </button>
        ))}
      </div>

      {/* Custom input */}
      <div className="flex items-center gap-3 mb-10">
        <span className="text-text-muted text-sm">or enter custom:</span>
        <input
          type="text"
          inputMode="numeric"
          value={inputVal}
          onChange={handleInput}
          maxLength={2}
          className="w-16 h-10 rounded-lg bg-muted border border-border text-center text-text-primary font-bold text-lg focus:outline-none focus:border-accent/60 transition-all"
        />
        <span className="text-text-muted text-xs">max {MAX}</span>
      </div>

      {/* CTA */}
      <button
        disabled={!valid}
        onClick={() => valid && onSubmit(count)}
        className={`flex items-center gap-2 px-8 py-3 rounded-xl font-semibold text-sm transition-all duration-200 ${
          valid
            ? 'bg-accent text-white hover:bg-accent/90 shadow-lg shadow-accent/30 hover:scale-105'
            : 'bg-muted text-text-muted border border-border cursor-not-allowed'
        }`}
      >
        <Zap size={15} />
        Generate {valid ? count : '–'} Recommendations
        <ChevronRight size={15} />
      </button>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────
export default function Recommendations() {
  const { handle, loading: ctxLoading } = useAnalytics();

  const [phase, setPhase] = useState('pick');      // 'pick' | 'loading' | 'results'
  const [count, setCount] = useState(10);
  const [data, setData] = useState([]);
  const [fetchError, setFetchError] = useState(null);
  const [filter, setFilter] = useState(ALL);
  const [refreshing, setRefreshing] = useState(false);

  const fetchRecs = useCallback(async (handle, limit, isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setPhase('loading');
    setFetchError(null);
    try {
      const recs = await analyticsApi.getRecommendations(handle, limit);
      setData(recs);
      setFilter(ALL);
      setPhase('results');
    } catch (err) {
      setFetchError(err.message || 'Failed to fetch recommendations.');
      setPhase('results');
    } finally {
      setRefreshing(false);
    }
  }, []);

  const handleSubmit = (n) => {
    setCount(n);
    fetchRecs(handle, n);
  };

  const handleRefresh = () => fetchRecs(handle, count, true);

  const handleReset = () => {
    setPhase('pick');
    setData([]);
    setFetchError(null);
  };

  // Not logged in / no handle
  if (!handle && !ctxLoading) return <NotSearchedState />;

  // ── Count picker ──
  if (phase === 'pick') return <CountPicker onSubmit={handleSubmit} />;

  // ── Loading ──
  if (phase === 'loading') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 animate-fade-in">
        <Loader2 size={40} className="text-accent animate-spin" />
        <p className="text-text-muted text-sm">Generating {count} personalised recommendations…</p>
      </div>
    );
  }

  // ── Results ──
  const tiers = [ALL, ...new Set(data.map(d => d.difficulty_tier).filter(Boolean))];
  const filtered = filter === ALL ? data : data.filter(d => d.difficulty_tier === filter);

  return (
    <div className="space-y-6 animate-fade-in pb-8">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <p className="text-text-muted text-sm mb-1">Recommendations</p>
          <h1 className="font-kalam font-bold text-3xl text-white">Problem Suggestions</h1>
        </div>
        <div className="flex items-center gap-2">
          {/* Refresh */}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            title="Refresh recommendations"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-muted border border-border text-sm text-text-secondary hover:border-accent/50 hover:text-text-primary transition-all duration-200 disabled:opacity-50"
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin text-accent' : ''} />
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
          {/* Change count */}
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent/10 border border-accent/20 text-sm text-accent hover:bg-accent/20 transition-all duration-200"
          >
            <Zap size={14} />
            Change count
          </button>
        </div>
      </div>

      {fetchError && (
        <div className="glass-card p-4 border border-red-500/30 text-red-400 text-sm">
          {fetchError}
        </div>
      )}

      {/* Show notice if backend returned fewer than requested */}
      {!fetchError && data.length > 0 && data.length < count && (
        <div className="glass-card p-3 border border-amber-500/30 text-amber-400 text-xs flex items-center gap-2">
          <Lightbulb size={13} className="shrink-0" />
          Only {data.length} unsolved problems match your profile — showing all available.
          Sync more Codeforces data to unlock more recommendations.
        </div>
      )}

      {/* Filter chips */}
      {data.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <Filter size={13} className="text-text-muted" />
          {tiers.map(t => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-all duration-200 ${
                filter === t
                  ? 'bg-accent text-white border-accent'
                  : 'bg-muted text-text-secondary border-border hover:border-accent/40 hover:text-text-primary'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      )}

      {/* Stats bar */}
      {data.length > 0 && (
        <div className="glass-card p-4 flex gap-6 text-sm flex-wrap">
          <div>
            <span className="text-text-muted">Showing</span>
            <span className="ml-2 font-bold text-text-primary">{filtered.length}</span>
            <span className="text-text-muted"> / {data.length}</span>
          </div>
          {['Easy Stretch', 'Current Level', 'Challenge'].map(t => {
            const c = data.filter(r => r.difficulty_tier === t).length;
            if (!c) return null;
            return (
              <div key={t}>
                <span className="text-text-muted">{t}</span>
                <span className="ml-2 font-bold text-text-primary">{c}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Cards */}
      {filtered.length === 0 ? (
        <EmptyState icon={Lightbulb} message="No recommendations match the current filter." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((rec, i) => (
            <RecommendationCard key={`${rec.problem_code}-${i}`} {...rec} />
          ))}
        </div>
      )}
    </div>
  );
}
