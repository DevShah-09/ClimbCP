const strengthConfig = {
  Expert:   { cls: 'badge-accent', dot: 'bg-accent' },
  Strong:   { cls: 'badge-success', dot: 'bg-emerald-400' },
  Moderate: { cls: 'badge-warning', dot: 'bg-amber-400' },
  Weak:     { cls: 'badge-danger', dot: 'bg-red-400' },
};

function ScoreBar({ value }) {
  const color = value >= 80 ? '#5227FF' : value >= 60 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${value}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs text-text-secondary w-8 text-right font-mono">{value}</span>
    </div>
  );
}

export default function TopicTable({ data = [], loading = false }) {
  if (loading) {
    return (
      <div className="glass-card p-5">
        <div className="skeleton h-5 w-32 rounded mb-4" />
        {[...Array(5)].map((_, i) => (
          <div key={i} className="skeleton h-10 w-full rounded mb-2" />
        ))}
      </div>
    );
  }

  return (
    <div className="glass-card p-5">
      <h3 className="section-title mb-4">Topic Breakdown</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-text-muted text-xs uppercase tracking-widest">
              <th className="text-left py-2 pr-4 font-medium">Topic</th>
              <th className="text-left py-2 pr-4 font-medium">Score</th>
              <th className="text-right py-2 pr-4 font-medium">Solved</th>
              <th className="text-right py-2 pr-4 font-medium">Accuracy</th>
              <th className="text-right py-2 font-medium">Level</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => {
              const cfg = strengthConfig[row.strength] || strengthConfig.Moderate;
              return (
                <tr
                  key={i}
                  className="border-b border-border/50 hover:bg-muted/50 transition-colors duration-150"
                >
                  <td className="py-3 pr-4 font-medium text-text-primary">{row.topic}</td>
                  <td className="py-3 pr-4 w-36">
                    <ScoreBar value={row.score} />
                  </td>
                  <td className="py-3 pr-4 text-right text-text-secondary font-mono">{row.solved}</td>
                  <td className="py-3 pr-4 text-right text-text-secondary">{row.accuracy}%</td>
                  <td className="py-3 text-right">
                    <span className={`badge ${cfg.cls}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                      {row.strength}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
