import React, { useState } from 'react';
import { useAnalytics } from '../hooks/AnalyticsContext';
import { aiApi } from '../services/api';
import { Sparkles, Trophy, TrendingDown, Target, Loader2, Info } from 'lucide-react';
import { EmptyState } from '../components/UIStates';

// --- Sub-components for each tab ---

function ContestReviewTab({ handle, ratingHistory }) {
  const [contestId, setContestId] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleGenerate = async (e) => {
    e.preventDefault();
    const query = contestId.trim();
    if (!query) return;

    let targetContestId = parseInt(query, 10);

    // If rating history is available, check if the input matches a contest name or ID
    if (ratingHistory) {
      const match = ratingHistory.find(c => 
        c.contest_id.toString() === query || 
        c.contest_name.toLowerCase().includes(query.toLowerCase())
      );
      if (match) {
        targetContestId = match.contest_id;
      }
    }

    if (isNaN(targetContestId)) {
      setError("Please enter a valid Contest ID or a round name/number from your history.");
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const res = await aiApi.getContestReview(handle, targetContestId);
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to generate contest review.');
    } finally {
      setLoading(false);
    }
  };

  const recentContests = ratingHistory?.slice().reverse().slice(0, 5) || [];

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-2">Contest Review</h3>
        <p className="text-sm text-text-secondary mb-4">
          Enter a Codeforces Contest ID (e.g., 1920) or a Round number (e.g., 954) to generate a personalized AI coaching report.
        </p>
        <form onSubmit={handleGenerate} className="flex gap-3 max-w-md">
          <input
            type="text"
            value={contestId}
            onChange={(e) => setContestId(e.target.value)}
            placeholder="Contest ID or Round No"
            className="flex-1 bg-surface border border-border rounded-lg px-4 py-2 text-text-primary focus:outline-none focus:border-accent"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-accent text-white px-5 py-2 rounded-lg font-medium hover:bg-accent/90 disabled:opacity-70 flex items-center gap-2"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            Generate
          </button>
        </form>
        {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
        
        {recentContests.length > 0 && (
          <div className="mt-6 pt-4 border-t border-border/50">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Recent Contests</h4>
            <div className="flex flex-wrap gap-2">
              {recentContests.map(c => (
                <button
                  key={c.contest_id}
                  onClick={() => setContestId(c.contest_id.toString())}
                  type="button"
                  className="text-xs bg-surface border border-border rounded-md px-3 py-1.5 hover:border-accent hover:text-accent transition-colors flex items-center gap-2 text-text-secondary cursor-pointer"
                >
                  <span className="truncate max-w-[200px]" title={c.contest_name}>{c.contest_name}</span>
                  <span className={`font-mono font-medium ${c.rating_change > 0 ? 'text-green-400' : c.rating_change < 0 ? 'text-red-400' : 'text-text-muted'}`}>
                    {c.rating_change > 0 ? '+' : ''}{c.rating_change}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {loading && (
        <div className="glass-card p-10 flex flex-col items-center justify-center gap-4 text-text-secondary">
          <Loader2 size={32} className="animate-spin text-accent" />
          <p>Analyzing your submissions, topic mastery, and contest data...</p>
        </div>
      )}

      {data && !loading && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="glass-card p-6">
            <h4 className="font-semibold text-text-primary text-lg mb-3 flex items-center gap-2">
              <Trophy size={20} className="text-accent" />
              Summary
            </h4>
            <p className="text-text-secondary leading-relaxed">{data.summary}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-card p-6 border-t-4 border-t-green-500/50">
              <h4 className="font-semibold text-text-primary mb-3">Strengths</h4>
              <ul className="list-disc pl-5 space-y-2 text-sm text-text-secondary">
                {data.strengths.map((item, i) => <li key={i}>{item}</li>)}
              </ul>
            </div>
            <div className="glass-card p-6 border-t-4 border-t-red-500/50">
              <h4 className="font-semibold text-text-primary mb-3">Weaknesses</h4>
              <ul className="list-disc pl-5 space-y-2 text-sm text-text-secondary">
                {data.weaknesses.map((item, i) => <li key={i}>{item}</li>)}
              </ul>
            </div>
          </div>

          <div className="glass-card p-6">
            <h4 className="font-semibold text-text-primary mb-3">Missed Opportunities</h4>
            <ul className="list-disc pl-5 space-y-2 text-sm text-text-secondary">
              {data.missed_opportunities.map((item, i) => <li key={i}>{item}</li>)}
            </ul>
          </div>

          <div className="glass-card p-6 border border-accent/20 bg-accent/5">
            <h4 className="font-semibold text-accent mb-3">Action Plan</h4>
            <ul className="space-y-3">
              {data.action_plan.map((item, i) => (
                <li key={i} className="flex gap-3 text-sm text-text-primary">
                  <span className="shrink-0 w-6 h-6 rounded-full bg-accent/20 text-accent flex items-center justify-center font-bold text-xs">
                    {i + 1}
                  </span>
                  <span className="mt-0.5">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}


function RatingLossTab({ handle }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await aiApi.getRatingLoss(handle);
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to fetch rating loss analysis.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {!data && !loading && (
        <div className="glass-card p-8 text-center flex flex-col items-center">
          <TrendingDown size={48} className="text-text-muted mb-4" />
          <h3 className="text-xl font-semibold text-text-primary mb-2">Rating Stagnation Analysis</h3>
          <p className="text-text-secondary max-w-md mx-auto mb-6">
            Stuck at your current rating? The AI coach will analyze your recent contests, submission habits, and topic mastery to explain why.
          </p>
          <button
            onClick={fetchAnalysis}
            className="bg-accent text-white px-6 py-2.5 rounded-lg font-medium hover:bg-accent/90 flex items-center gap-2"
          >
            <Sparkles size={18} />
            Analyze Rating Trend
          </button>
          {error && <p className="text-red-400 text-sm mt-4">{error}</p>}
        </div>
      )}

      {loading && (
        <div className="glass-card p-10 flex flex-col items-center justify-center gap-4 text-text-secondary">
          <Loader2 size={32} className="animate-spin text-accent" />
          <p>Crunching rating history and activity statistics...</p>
        </div>
      )}

      {data && !loading && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="glass-card p-6 flex flex-col md:flex-row items-center gap-6 text-center md:text-left">
            <div className={`w-24 h-24 rounded-full flex flex-col items-center justify-center shrink-0 border-4 ${data.rating_change < 0 ? 'border-red-500/30 bg-red-500/10 text-red-400' : 'border-text-muted/30 bg-surface text-text-primary'}`}>
              <span className="text-xs font-semibold uppercase tracking-wider opacity-70">Net Change</span>
              <span className="text-2xl font-bold">{data.rating_change > 0 ? '+' : ''}{data.rating_change}</span>
            </div>
            <div>
              <h4 className="font-semibold text-text-primary text-lg mb-2">Coach's Explanation</h4>
              <p className="text-text-secondary leading-relaxed">{data.explanation}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-card p-6">
              <h4 className="font-semibold text-text-primary mb-4 flex items-center gap-2">
                <Info size={18} className="text-text-muted" />
                Major Causes
              </h4>
              <ul className="space-y-3">
                {data.major_causes.map((item, i) => (
                  <li key={i} className="bg-surface/50 p-3 rounded-lg border border-border text-sm text-text-secondary">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="glass-card p-6 border border-accent/20 bg-accent/5">
              <h4 className="font-semibold text-accent mb-4 flex items-center gap-2">
                <Target size={18} />
                Recommended Actions
              </h4>
              <ul className="space-y-3">
                {data.recommended_actions.map((item, i) => (
                  <li key={i} className="flex gap-3 text-sm text-text-primary bg-surface/50 p-3 rounded-lg border border-accent/10">
                    <span className="shrink-0 w-5 h-5 rounded-full bg-accent/20 text-accent flex items-center justify-center font-bold text-xs mt-0.5">
                      {i + 1}
                    </span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


function BottlenecksTab({ handle }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await aiApi.getBottlenecks(handle);
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to fetch bottleneck analysis.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {!data && !loading && (
        <div className="glass-card p-8 text-center flex flex-col items-center">
          <Target size={48} className="text-text-muted mb-4" />
          <h3 className="text-xl font-semibold text-text-primary mb-2">Performance Bottlenecks</h3>
          <p className="text-text-secondary max-w-md mx-auto mb-6">
            Discover the exact factors holding back your progress. We analyze topics, solving speed, implementation accuracy, and upsolving habits.
          </p>
          <button
            onClick={fetchAnalysis}
            className="bg-accent text-white px-6 py-2.5 rounded-lg font-medium hover:bg-accent/90 flex items-center gap-2"
          >
            <Sparkles size={18} />
            Identify Bottlenecks
          </button>
          {error && <p className="text-red-400 text-sm mt-4">{error}</p>}
        </div>
      )}

      {loading && (
        <div className="glass-card p-10 flex flex-col items-center justify-center gap-4 text-text-secondary">
          <Loader2 size={32} className="animate-spin text-accent" />
          <p>Running algorithmic pre-scoring and generating narrative...</p>
        </div>
      )}

      {data && !loading && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="glass-card p-6">
            <h4 className="font-semibold text-text-primary text-lg mb-3">Coach's Assessment</h4>
            <p className="text-text-secondary leading-relaxed">{data.narrative}</p>
          </div>

          <div className="space-y-3">
            <h4 className="font-semibold text-text-primary px-1">Factor Breakdown</h4>
            {data.bottlenecks.map((item, i) => (
              <div key={i} className="glass-card p-4 flex flex-col md:flex-row gap-4 md:items-center">
                <div className="md:w-1/4 shrink-0">
                  <h5 className="font-semibold text-text-primary text-sm">{item.factor}</h5>
                </div>
                
                <div className="flex-1">
                  <p className="text-xs text-text-secondary mb-2">{item.description}</p>
                  <div className="h-2 w-full bg-surface rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${item.impact > 70 ? 'bg-red-500' : item.impact > 40 ? 'bg-yellow-500' : 'bg-green-500'}`}
                      style={{ width: `${item.impact}%` }}
                    />
                  </div>
                </div>
                
                <div className="md:w-16 shrink-0 text-right">
                  <span className="text-xl font-bold text-text-primary">{item.impact}</span>
                  <span className="text-[10px] text-text-muted block uppercase tracking-wider">Impact</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


// --- Main Page Component ---

export default function AiCoach() {
  const { handle, ratingHistory } = useAnalytics();
  const [activeTab, setActiveTab] = useState('contest');

  if (!handle) return null;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-text-primary mb-2 flex items-center gap-3">
          <Sparkles className="text-accent" size={28} />
          AI Coach
        </h1>
        <p className="text-text-secondary">
          Personalized, data-driven coaching insights powered by LLMs.
        </p>
      </header>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border mb-6 overflow-x-auto pb-1 hide-scrollbar">
        {[
          { id: 'contest', label: 'Contest Review' },
          { id: 'rating', label: 'Rating Analysis' },
          { id: 'bottleneck', label: 'Bottleneck Analysis' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors border-b-2 ${
              activeTab === tab.id
                ? 'text-accent border-accent bg-accent/5'
                : 'text-text-muted border-transparent hover:text-text-primary hover:bg-surface'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'contest' && <ContestReviewTab handle={handle} ratingHistory={ratingHistory} />}
        {activeTab === 'rating' && <RatingLossTab handle={handle} />}
        {activeTab === 'bottleneck' && <BottlenecksTab handle={handle} />}
      </div>
    </div>
  );
}
