import { useEffect, useState, useCallback } from 'react';
import { Users, Sparkles, Award, Target, BrainCircuit, ExternalLink, Flame, TrendingUp } from 'lucide-react';
import { useAnalytics } from '../hooks/AnalyticsContext';
import { usersApi, embeddingsApi } from '../services/api';
import { LoadingSpinner, ErrorState, NotSearchedState } from '../components/UIStates';
import ProblemDetailsModal from '../components/ProblemDetailsModal';

export default function SimilarUsers() {
  const { handle, loading: ctxLoading } = useAnalytics();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Re-running user embedding generation state
  const [rebuilding, setRebuilding] = useState(false);

  // Selected problem for similarity modal
  const [selectedProblem, setSelectedProblem] = useState(null);

  const fetchSimilarData = useCallback(async (isRebuilding = false) => {
    if (!handle) return;
    if (isRebuilding) {
      setRebuilding(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      if (isRebuilding) {
        // Force regenerate user embedding first
        await embeddingsApi.generateUser(handle);
      }
      const resp = await usersApi.getSimilar(handle);
      setData(resp);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to load similar users and peer insights.');
    } finally {
      setLoading(false);
      setRebuilding(false);
    }
  }, [handle]);

  useEffect(() => {
    fetchSimilarData();
  }, [fetchSimilarData]);

  if (!handle && !ctxLoading) {
    return <NotSearchedState />;
  }

  if (loading) {
    return <LoadingSpinner message="Locating peers with similar performance vectors..." />;
  }

  if (error && !rebuilding) {
    return <ErrorState message={error} onRetry={() => fetchSimilarData(false)} />;
  }

  const similarUsers = data?.similar_users ?? [];
  const insights = data?.insights ?? [];
  const recommendedProblems = data?.recommended_problems ?? [];

  // Codeforces user link helper
  const getCfUserUrl = (userHandle) => `https://codeforces.com/profile/${userHandle}`;

  return (
    <div className="space-y-6 animate-fade-in pb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <p className="text-text-muted text-sm mb-1">Semantic Intelligence</p>
          <h1 className="font-kalam font-bold text-3xl text-white">Similar Users & Insights</h1>
        </div>

        <button
          onClick={() => fetchSimilarData(true)}
          disabled={rebuilding}
          className="px-4 py-2 rounded-lg bg-surface/80 border border-border text-xs text-text-secondary hover:text-white hover:border-accent/40 transition-all cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
        >
          <Sparkles size={13} className={`text-accent ${rebuilding ? 'animate-spin' : ''}`} />
          {rebuilding ? 'Recalculating...' : 'Refresh Peer Analytics'}
        </button>
      </div>

      {rebuilding && (
        <div className="glass-card p-4 border border-accent/20 bg-accent/5 flex items-center gap-3 animate-pulse">
          <BrainCircuit size={18} className="text-accent animate-spin" />
          <p className="text-sm text-text-secondary">Regenerating user embedding profile and calculating peer cosine similarity...</p>
        </div>
      )}

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Similar Users Grid */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="font-semibold text-white flex items-center gap-2">
            <Users size={18} className="text-accent" />
            Top Similar Profiles
          </h3>

          {similarUsers.length === 0 ? (
            <div className="glass-card p-8 text-center border-border/40">
              <p className="text-sm text-text-muted">No similar profiles found. Please register other users in ClimbCP to see peers.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {similarUsers.map((peer, idx) => (
                <div key={peer.handle || idx} className="glass-card p-5 border border-border/80 flex flex-col justify-between gap-4 hover:-translate-y-0.5 transition-all">
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <a 
                          href={getCfUserUrl(peer.handle)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono font-bold text-lg text-white hover:text-accent flex items-center gap-1 group"
                        >
                          {peer.handle}
                          <ExternalLink size={12} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                        </a>
                        <p className="text-xs text-text-muted mt-0.5">Codeforces Peer</p>
                      </div>
                      <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded border border-emerald-500/15">
                        {Math.round(peer.similarity * 100)}% Match
                      </span>
                    </div>

                    {/* Similarity bar */}
                    <div className="w-full h-1.5 rounded-full bg-border/40 overflow-hidden">
                      <div 
                        className="h-full rounded-full bg-emerald-500"
                        style={{ width: `${peer.similarity * 100}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex items-center gap-6 pt-3 border-t border-border/60 text-xs">
                    <div>
                      <p className="text-text-muted text-[10px]">Current Rating</p>
                      <p className="font-semibold text-white mt-0.5 font-mono">{peer.rating}</p>
                    </div>
                    <div>
                      <p className="text-text-muted text-[10px]">Peak Rating</p>
                      <p className="font-semibold text-text-secondary mt-0.5 font-mono">{peer.max_rating}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Actionable Insights Panel */}
        <div className="glass-card p-6 border-accent/15 bg-gradient-to-b from-accent/5 to-transparent flex flex-col justify-between">
          <div className="space-y-4">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Award size={18} className="text-accent" />
              Actionable Peer Insights
            </h3>
            <p className="text-xs text-text-muted">
              Grounded in the solve discrepancies between your profile and matching peers.
            </p>

            <div className="space-y-3 pt-2">
              {insights.map((insight, i) => (
                <div key={i} className="flex gap-2.5 items-start p-3 rounded-lg bg-surface/40 border border-border/60">
                  <TrendingUp size={14} className="text-accent mt-0.5 shrink-0" />
                  <p className="text-xs text-text-secondary leading-normal">{insight}</p>
                </div>
              ))}
              {insights.length === 0 && (
                <p className="text-xs text-text-muted text-center py-4">No peer insights available.</p>
              )}
            </div>
          </div>

          <div className="pt-6 border-t border-border/80 text-[10px] text-text-muted flex items-center gap-1.5">
            <Target size={12} />
            Updated dynamically based on vector distances
          </div>
        </div>
      </div>

      {/* Peer Problem Recommendations */}
      <div className="space-y-4 pt-2">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Target size={18} className="text-accent" />
          Recommended Solved by Peers
        </h3>

        {recommendedProblems.length === 0 ? (
          <div className="glass-card p-8 text-center border-border/40">
            <p className="text-sm text-text-muted">No custom peer problem suggestions available. Run Codeforces Sync to load additional data.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recommendedProblems.map((prob, idx) => (
              <div 
                key={prob.problem_id || idx}
                onClick={() => setSelectedProblem({
                  id: prob.problem_id,
                  name: prob.name,
                  rating: prob.rating,
                  problem_code: prob.problem_code
                })}
                className="glass-card p-4 border border-border/60 hover:border-accent/40 hover:bg-surface/50 transition-all cursor-pointer flex flex-col justify-between gap-3 group"
              >
                <div className="space-y-1.5">
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="font-mono font-semibold text-sm text-white group-hover:text-accent transition-colors truncate max-w-[200px]">
                      {prob.name}
                    </h4>
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold font-mono text-accent bg-accent/10 px-2 py-0.5 rounded shrink-0">
                      <Flame size={10} />
                      *{prob.rating}
                    </span>
                  </div>
                  <p className="text-xs text-text-muted font-mono">{prob.problem_code}</p>
                </div>

                <div className="pt-2 border-t border-border/40 text-[11px] text-text-secondary italic">
                  {prob.reason}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Details & Similar Problems Modal */}
      {selectedProblem && (
        <ProblemDetailsModal
          isOpen={!!selectedProblem}
          onClose={() => setSelectedProblem(null)}
          problemId={selectedProblem.id}
          problemName={selectedProblem.name}
          rating={selectedProblem.rating}
          problemCode={selectedProblem.problem_code}
        />
      )}
    </div>
  );
}
