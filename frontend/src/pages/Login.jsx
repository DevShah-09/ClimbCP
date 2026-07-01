import { useState } from 'react';
import { useAnalytics } from '../hooks/AnalyticsContext';
import { Trophy, Loader2, AlertCircle, Sparkles, ArrowRight, Zap } from 'lucide-react';

export default function Login() {
  const { enterHandle, loading, syncing, error } = useAnalytics();
  const [inputHandle, setInputHandle] = useState('');
  const [localError, setLocalError] = useState(null);

  const isProcessing = loading || syncing;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError(null);

    const h = inputHandle.trim();
    if (!h) {
      setLocalError('Please enter your Codeforces handle');
      return;
    }
    if (!/^[a-zA-Z0-9_.-]+$/.test(h)) {
      setLocalError('Invalid handle format — only letters, numbers, _, -, . allowed');
      return;
    }

    const success = await enterHandle(h);
    if (!success && error) {
      setLocalError(error);
    }
  };

  const displayError = localError || error;

  const statusMessage = syncing
    ? 'Syncing your Codeforces data...'
    : loading
    ? 'Loading your analytics...'
    : null;

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Background ambient glows */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-accent/10 blur-[120px] opacity-70 animate-pulse-slow" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-accent-pink/5 blur-[120px] opacity-60" />
      </div>

      <div className="relative z-10 w-full max-w-md animate-slide-up">
        {/* Brand Header */}
        <div className="flex flex-col items-center gap-3 mb-8 text-center">
          <div className="w-16 h-16 rounded-2xl bg-accent flex items-center justify-center shadow-lg shadow-accent/20 border border-accent/30 relative">
            <Trophy size={28} className="text-white" />
            <div className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-accent-pink flex items-center justify-center animate-bounce">
              <Sparkles size={10} className="text-black" />
            </div>
          </div>
          <div>
            <h1 className="font-kalam font-bold text-4xl text-white tracking-wide mb-1">
              ClimbCP
            </h1>
            <p className="text-sm text-text-secondary font-medium tracking-wide">
              Competitive Programming Analytics &amp; Intelligence
            </p>
          </div>
        </div>

        {/* Main Card */}
        <div className="glass-card p-8 rounded-xl border border-border space-y-6">
          <div className="space-y-1.5">
            <h2 className="text-xl font-semibold text-text-primary">
              Enter your Codeforces handle
            </h2>
            <p className="text-xs text-text-muted leading-relaxed">
              We'll sync your submissions, rating history, and contest data directly from Codeforces. No account needed.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="handle-input" className="text-[10px] font-bold uppercase tracking-wider text-text-muted flex items-center gap-1">
                <Trophy size={11} /> Codeforces Handle
              </label>
              <input
                id="handle-input"
                type="text"
                autoFocus
                autoComplete="off"
                spellCheck={false}
                placeholder="e.g. tourist, Benq, jiangly"
                value={inputHandle}
                onChange={(e) => { setInputHandle(e.target.value); setLocalError(null); }}
                disabled={isProcessing}
                className="w-full bg-muted border border-border rounded-lg px-3.5 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent focus:bg-card/40 transition-all font-mono"
              />
            </div>

            {/* Status / Error */}
            {isProcessing && statusMessage && (
              <div className="flex items-center gap-2.5 p-3 rounded-lg bg-accent/10 border border-accent/20 text-accent text-xs animate-fade-in">
                <Loader2 size={14} className="animate-spin shrink-0" />
                <span>{statusMessage}</span>
              </div>
            )}

            {!isProcessing && displayError && (
              <div className="flex items-start gap-2.5 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs animate-fade-in">
                <AlertCircle size={14} className="shrink-0 mt-0.5" />
                <span>{displayError}</span>
              </div>
            )}

            <button
              id="submit-handle-btn"
              type="submit"
              disabled={isProcessing}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-lg bg-accent text-white font-semibold text-sm hover:bg-accent/90 disabled:bg-accent/40 active:translate-y-0.5 transition-all shadow-md shadow-accent/20 cursor-pointer"
            >
              {isProcessing ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>{syncing ? 'Syncing data...' : 'Loading analytics...'}</span>
                </>
              ) : (
                <>
                  <Zap size={15} />
                  <span>Analyse my profile</span>
                  <ArrowRight size={15} />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Feature pills */}
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {['Rating history', 'Topic mastery', 'AI coaching', 'Similar users', 'Recommendations'].map(f => (
            <span key={f} className="text-[10px] font-medium text-text-muted border border-border/60 rounded-full px-3 py-1 bg-card/20">
              {f}
            </span>
          ))}
        </div>

        <p className="text-center text-xs text-text-muted mt-5 tracking-wide">
          ClimbCP syncs profile data, rating history, and all submissions in real-time.
        </p>
      </div>
    </div>
  );
}
