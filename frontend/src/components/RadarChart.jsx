import {
  Radar, RadarChart as RechartsRadar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip
} from 'recharts';

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-card p-3 text-xs">
      <p className="font-semibold text-text-primary">{payload[0].payload.topic}</p>
      <p className="text-accent mt-1">Score: <span className="text-white font-bold">{payload[0].value}</span></p>
    </div>
  );
};

export default function RadarChart({ data = [], loading = false }) {
  if (loading) {
    return (
      <div className="glass-card p-5">
        <div className="skeleton h-5 w-36 rounded mb-4" />
        <div className="skeleton h-64 w-full rounded" />
      </div>
    );
  }

  const chartData = data.map(d => ({
    topic: d.topic?.split(' ')[0] ?? d.topic,
    score: d.score ?? 0,
    fullMark: 100,
  }));

  return (
    <div className="glass-card p-5">
      <h3 className="section-title mb-4">Topic Mastery Radar</h3>
      <ResponsiveContainer width="100%" height={280}>
        <RechartsRadar data={chartData} cx="50%" cy="50%" outerRadius="75%">
          <PolarGrid stroke="#1f1f1f" />
          <PolarAngleAxis
            dataKey="topic"
            tick={{ fill: '#a1a1aa', fontSize: 11, fontFamily: 'Inter' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Radar
            dataKey="score"
            stroke="#5227FF"
            fill="#5227FF"
            fillOpacity={0.18}
            strokeWidth={2}
          />
        </RechartsRadar>
      </ResponsiveContainer>
    </div>
  );
}
