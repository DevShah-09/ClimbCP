import { useState, useEffect } from 'react';
import { useAnalytics } from '../hooks/AnalyticsContext';
import { Trophy, Loader2, AlertCircle, Sparkles } from 'lucide-react';

export default function Login() {
  const { fetchAllData, loading, error } = useAnalytics();
  const [input, setInput] = useState('');
  const [localError, setLocalError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const handle = input.trim();
    if (!handle) {
      setLocalError('Please enter a handle');
      return;
    }
    setLocalError(null);
    
    const success = await fetchAllData(handle);
    if (!success && error) {
      setLocalError(error);
    }
  };

  // Sync context error to local display
  useEffect(() => {
    if (error) setLocalError(error);
  }, [error]);

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Background ambient glows */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-accent/10 blur-[120px] opacity-70 animate-pulse-slow" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-accent-pink/5 blur-[120px] opacity-60" />
      </div>

      {/* Main card */}
      <div className="relative z-10 w-full max-w-md animate-slide-up">
        {/* Brand Header */}
        <div className="flex flex-col items-center gap-3 mb-8 text-center">
          <div className="w-14 h-14 rounded-2xl bg-accent flex items-center justify-center shadow-lg shadow-accent/20 border border-accent/30 relative">
            <Trophy size={26} className="text-white" />
            <div className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-accent-pink flex items-center justify-center animate-bounce">
              <Sparkles size={10} className="text-black" />
            </div>
          </div>
          <div>
            <h1 className="font-kalam font-bold text-4xl text-white tracking-wide mb-1">
              ClimbCP
            </h1>
            <p className="text-sm text-text-secondary font-medium tracking-wide">
              Competitive Programming Analytics & Intelligence
            </p>
          </div>
        </div>

        {/* Glassmorphic Login Form */}
        <div className="glass-card p-6 md:p-8 space-y-6">
          <div className="space-y-2">
            <h2 className="text-lg font-semibold text-text-primary">Welcome back</h2>
            <p className="text-xs text-text-muted">
              Enter your Codeforces handle to synchronize your contest records and analyze your weaknesses.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="handle-input" className="text-xs font-semibold uppercase tracking-wider text-text-muted">
                Codeforces Handle
              </label>
              <div className="relative">
                <input
                  id="handle-input"
                  type="text"
                  autoFocus
                  placeholder="e.g. tourist, Benq, DevShah"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={loading}
                  className="w-full bg-muted border border-border rounded-lg px-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent focus:bg-card/40 transition-all font-mono"
                />
              </div>
            </div>

            {localError && (
              <div className="flex items-start gap-2.5 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs animate-fade-in">
                <AlertCircle size={14} className="shrink-0 mt-0.5" />
                <span>{localError}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-accent text-white font-semibold text-sm hover:bg-accent/90 disabled:bg-accent/40 active:translate-y-0.5 transition-all shadow-md shadow-accent/20 cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Synchronizing contest data...</span>
                </>
              ) : (
                <span>Verify & Enter Dashboard</span>
              )}
            </button>
          </form>
        </div>

        {/* Footnote */}
        <p className="text-center text-xs text-text-muted mt-6 tracking-wide">
          ClimbCP operates entirely on local records synchronized with Codeforces.
        </p>
      </div>
    </div>
  );
}
