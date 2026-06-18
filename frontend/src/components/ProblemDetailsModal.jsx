import { useEffect, useState } from 'react';
import { X, ExternalLink, Flame, Info } from 'lucide-react';
import { problemsApi } from '../services/api';
import { LoadingSpinner, ErrorState } from './UIStates';

export default function ProblemDetailsModal({ isOpen, onClose, problemId, problemName, rating, problemCode }) {
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && problemId) {
      setLoading(true);
      setError(null);
      problemsApi.getSimilar(problemId)
        .then((data) => {
          setSimilar(data.similar_problems ?? []);
          setLoading(false);
        })
        .catch((err) => {
          console.error(err);
          setError('Failed to load semantically similar problems.');
          setLoading(false);
        });
    }
  }, [isOpen, problemId]);

  if (!isOpen) return null;

  // Codeforces problem link helper
  // e.g. "1845A" -> contest 1845, index A
  const getCodeforcesUrl = (code) => {
    if (!code) return '#';
    const match = code.match(/^(\d+)([A-Z]\d*)$/);
    if (match) {
      const [_, contestId, problemIndex] = match;
      return `https://codeforces.com/problemset/problem/${contestId}/${problemIndex}`;
    }
    return `https://codeforces.com/problemset`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay */}
      <div 
        className="absolute inset-0 bg-background/80 backdrop-blur-md" 
        onClick={onClose} 
      />

      {/* Modal Content */}
      <div className="relative glass-card w-full max-w-lg overflow-hidden border border-border/80 shadow-2xl flex flex-col z-10 max-h-[85vh] animate-fade-in">
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-border">
          <div>
            <span className="text-xs text-accent font-semibold tracking-wider uppercase">Problem Profile</span>
            <h3 className="font-kalam font-bold text-xl text-white mt-1 leading-snug">{problemName}</h3>
            {rating && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-accent/15 text-accent mt-2">
                <Flame size={12} />
                Rating: {rating}
              </span>
            )}
          </div>
          <button 
            onClick={onClose} 
            className="p-1.5 rounded-lg bg-muted text-text-muted hover:text-white transition-colors cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Solve Link */}
          <div className="p-4 rounded-xl bg-accent/5 border border-accent/10 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs text-text-muted">Target Platform</p>
              <p className="font-mono text-sm text-white">Codeforces ({problemCode})</p>
            </div>
            <a
              href={getCodeforcesUrl(problemCode)}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent hover:bg-accent-hover text-white text-xs font-medium transition-all shadow-md"
            >
              Open on Codeforces
              <ExternalLink size={12} />
            </a>
          </div>

          {/* Similar Problems Section */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-text-primary flex items-center gap-1.5 border-b border-border pb-2">
              <Info size={14} className="text-accent" />
              Semantically Similar Problems
            </h4>

            {loading && <LoadingSpinner message="Searching vector space for matches..." size={18} />}

            {error && <ErrorState message={error} />}

            {!loading && !error && similar.length === 0 && (
              <p className="text-xs text-text-muted text-center py-6">No similar problems found in database.</p>
            )}

            {!loading && !error && similar.length > 0 && (
              <div className="space-y-2.5">
                {similar.map((p, index) => (
                  <div 
                    key={p.problem_id || index}
                    className="p-3.5 rounded-xl bg-surface/50 border border-border/60 flex items-center justify-between hover:border-accent/30 hover:bg-surface/75 transition-all group"
                  >
                    <div className="space-y-1">
                      <p className="font-mono font-medium text-xs text-white group-hover:text-accent transition-colors leading-tight">
                        {p.name}
                      </p>
                      {p.rating && <p className="text-[10px] text-text-muted">Rating: {p.rating}</p>}
                    </div>

                    <div className="text-right shrink-0">
                      <p className="text-xs font-semibold text-emerald-400 font-mono">
                        {Math.round(p.similarity * 100)}% Match
                      </p>
                      <p className="text-[9px] text-text-muted">Cosine Similarity</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border bg-muted/30 text-right">
          <button 
            onClick={onClose} 
            className="px-4 py-2 text-xs font-medium text-text-secondary hover:text-white rounded-lg bg-muted border border-border transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
