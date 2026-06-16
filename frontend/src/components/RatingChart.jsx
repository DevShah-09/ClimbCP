import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area, AreaChart
} from 'recharts';
import { format, parseISO } from 'date-fns';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const change = d.rating_change;
  const changeColor = change > 0 ? '#34d399' : change < 0 ? '#f87171' : '#a1a1aa';

  return (
    <div className="glass-card p-3 text-xs space-y-1 min-w-[180px]">
      <p className="font-semibold text-text-primary truncate">{d.contest_name}</p>
      <p className="text-text-muted">{d.contest_date}</p>
      <div className="flex items-center justify-between pt-1 border-t border-border">
        <span className="text-text-secondary">Rating</span>
        <span className="font-bold text-white">{d.new_rating}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-text-secondary">Change</span>
        <span className="font-semibold" style={{ color: changeColor }}>
          {change > 0 ? '+' : ''}{change}
        </span>
      </div>
      {d.rank && (
        <div className="flex items-center justify-between">
          <span className="text-text-secondary">Rank</span>
          <span className="text-text-primary">#{d.rank}</span>
        </div>
      )}
    </div>
  );
};

export default function RatingChart({ data = [], loading = false }) {
  if (loading) {
    return (
      <div className="glass-card p-5">
        <div className="skeleton h-5 w-32 rounded mb-4" />
        <div className="skeleton h-56 w-full rounded" />
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="glass-card p-5 flex items-center justify-center h-72">
        <p className="text-text-muted text-sm">No rating history available</p>
      </div>
    );
  }

  const minRating = Math.min(...data.map(d => d.old_rating || d.new_rating));
  const maxRating = Math.max(...data.map(d => d.new_rating));

  return (
    <div className="glass-card p-5">
      <h3 className="section-title mb-4">Rating History</h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="ratingGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#5227FF" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#5227FF" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f1f1f" vertical={false} />
          <XAxis
            dataKey="contest_date"
            tick={{ fontSize: 10, fill: '#71717a' }}
            tickLine={false}
            axisLine={{ stroke: '#1f1f1f' }}
            tickFormatter={(v) => {
              try { return format(parseISO(v), 'MMM yy'); } catch { return v; }
            }}
          />
          <YAxis
            domain={[minRating - 50, maxRating + 100]}
            tick={{ fontSize: 10, fill: '#71717a' }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="new_rating"
            stroke="#5227FF"
            strokeWidth={2}
            fill="url(#ratingGrad)"
            dot={false}
            activeDot={{ r: 5, fill: '#5227FF', stroke: '#000', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
