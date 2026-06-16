import {
  Star, Trophy, BarChart2, CheckSquare, Target,
  TrendingUp, TrendingDown, Calendar, Flame, Zap
} from 'lucide-react';
import { useAnalytics } from '../hooks/AnalyticsContext';
import SummaryCard from '../components/SummaryCard';
import RatingChart from '../components/RatingChart';
import { LoadingSpinner, ErrorState, NotSearchedState } from '../components/UIStates';

function ContestStatsRow({ contestStats, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-20 rounded-xl" />)}
      </div>
    );
  }
  if (!contestStats) return null;

  const items = [
    { label: 'Avg Rank',     value: contestStats.average_rank ? `#${Math.round(contestStats.average_rank)}` : '—' },
    { label: 'Best Rank',    value: contestStats.best_rank ? `#${contestStats.best_rank}` : '—' },
    { label: 'Worst Rank',   value: contestStats.worst_rank ? `#${contestStats.worst_rank}` : '—' },
    { label: 'Rating Gains', value: contestStats.rating_increases ?? '—' },
    { label: 'Rating Losses',value: contestStats.rating_decreases ?? '—' },
    { label: 'Total Gained', value: contestStats.total_rating_gained ? `+${contestStats.total_rating_gained}` : '—' },
    { label: 'Total Lost',   value: contestStats.total_rating_lost ? `-${contestStats.total_rating_lost}` : '—' },
    { label: 'Net Change',   value: contestStats.total_rating_gained && contestStats.total_rating_lost
      ? `+${contestStats.total_rating_gained - contestStats.total_rating_lost}` : '—' },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {items.map(({ label, value }) => (
        <div key={label} className="glass-card p-3.5 flex flex-col gap-1">
          <span className="text-xs text-text-muted uppercase tracking-widest">{label}</span>
          <span className="text-xl font-bold font-mono text-text-primary">{value}</span>
        </div>
      ))}
    </div>
  );
}

function ActivityRow({ activityStats, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-24 rounded-xl" />)}
      </div>
    );
  }
  if (!activityStats) return null;

  const items = [
    { icon: Calendar, label: 'Active Days',           value: activityStats.active_days?.toLocaleString() ?? '—', color: 'accent' },
    { icon: Zap,      label: 'Avg Submissions / Day', value: activityStats.average_submissions_per_day ?? '—',    color: 'pink' },
    { icon: Flame,    label: 'Avg Solved / Week',     value: activityStats.average_solved_per_week ?? '—',        color: 'purple' },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {items.map(({ icon: Icon, label, value, color }) => (
        <SummaryCard key={label} icon={Icon} label={label} value={value} accentColor={color} />
      ))}
    </div>
  );
}

export default function Dashboard() {
  const { analytics, ratingHistory, contestStats, activityStats, loading, error, handle } = useAnalytics();

  if (!handle && !loading) return <NotSearchedState />;
  if (loading) return <LoadingSpinner message={`Loading analytics for ${handle}…`} />;
  if (error) return <ErrorState message={error} />;
  if (!analytics) return <NotSearchedState />;

  return (
    <div className="space-y-6 animate-fade-in pb-8">
      {/* Page header */}
      <div>
        <p className="text-text-muted text-sm mb-1">Dashboard</p>
        <h1 className="font-kalam font-bold text-3xl text-white">
          {handle}'s Analytics
        </h1>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          icon={Star}
          label="Current Rating"
          value={analytics.current_rating ?? '—'}
          accentColor="accent"
        />
        <SummaryCard
          icon={Trophy}
          label="Max Rating"
          value={analytics.max_rating ?? '—'}
          accentColor="pink"
        />
        <SummaryCard
          icon={BarChart2}
          label="Contests"
          value={analytics.contest_count?.toLocaleString() ?? '—'}
          accentColor="purple"
        />
        <SummaryCard
          icon={CheckSquare}
          label="Problems Solved"
          value={analytics.problems_solved?.toLocaleString() ?? '—'}
          accentColor="emerald"
        />
      </div>

      {/* Submission stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          icon={Target}
          label="Total Submissions"
          value={analytics.total_submissions?.toLocaleString() ?? '—'}
          accentColor="accent"
        />
        <SummaryCard
          icon={TrendingUp}
          label="Accepted"
          value={analytics.successful_submissions?.toLocaleString() ?? '—'}
          accentColor="emerald"
        />
        <SummaryCard
          icon={TrendingDown}
          label="Failed"
          value={analytics.failed_submissions?.toLocaleString() ?? '—'}
          accentColor="amber"
        />
        <SummaryCard
          icon={CheckSquare}
          label="Acceptance Rate"
          value={analytics.acceptance_rate != null ? `${analytics.acceptance_rate}%` : '—'}
          accentColor="pink"
        />
      </div>

      {/* Rating chart */}
      <RatingChart data={ratingHistory ?? []} />

      {/* Contest statistics */}
      <div>
        <h2 className="font-kalam font-bold text-xl text-white mb-3">Contest Statistics</h2>
        <ContestStatsRow contestStats={contestStats} loading={false} />
      </div>

      {/* Activity statistics */}
      <div>
        <h2 className="font-kalam font-bold text-xl text-white mb-3">Activity Statistics</h2>
        {activityStats && (
          <div className="glass-card p-4 mb-3 text-xs text-text-muted flex gap-6">
            {activityStats.first_activity_date && (
              <span>First activity: <span className="text-text-secondary">{activityStats.first_activity_date}</span></span>
            )}
            {activityStats.last_activity_date && (
              <span>Last activity: <span className="text-text-secondary">{activityStats.last_activity_date}</span></span>
            )}
          </div>
        )}
        <ActivityRow activityStats={activityStats} loading={false} />
      </div>
    </div>
  );
}
