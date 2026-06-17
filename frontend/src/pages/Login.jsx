import { useState, useEffect } from 'react';
import { useAnalytics } from '../hooks/AnalyticsContext';
import { Trophy, Loader2, AlertCircle, Sparkles, User, Mail, Lock, Key } from 'lucide-react';

export default function Login() {
  const { login, register, loading, error } = useAnalytics();
  const [isRegistering, setIsRegistering] = useState(false);
  
  // Form States
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [codeforcesHandle, setCodeforcesHandle] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [localError, setLocalError] = useState(null);

  // Sync context error to local display
  useEffect(() => {
    if (error) setLocalError(error);
  }, [error]);

  const handleToggleMode = () => {
    setIsRegistering(!isRegistering);
    setLocalError(null);
    setPassword('');
    setConfirmPassword('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError(null);

    // Common validations
    if (isRegistering) {
      if (!username.trim() || !email.trim() || !codeforcesHandle.trim() || !password || !confirmPassword) {
        setLocalError('All fields are required');
        return;
      }
      if (password.length < 6) {
        setLocalError('Password must be at least 6 characters');
        return;
      }
      if (password !== confirmPassword) {
        setLocalError('Passwords do not match');
        return;
      }
      
      const success = await register(
        username.trim(),
        email.trim(),
        codeforcesHandle.trim(),
        password
      );
      if (!success && error) {
        setLocalError(error);
      }
    } else {
      if (!username.trim() || !password) {
        setLocalError('Please fill in all fields');
        return;
      }
      const success = await login(username.trim(), password);
      if (!success && error) {
        setLocalError(error);
      }
    }
  };

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
        <div className="flex flex-col items-center gap-3 mb-6 text-center">
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

        {/* Tab Selection */}
        <div className="flex bg-muted p-1 rounded-t-xl border-t border-x border-border max-w-md w-full">
          <button
            type="button"
            onClick={() => { setIsRegistering(false); setLocalError(null); }}
            className={`flex-1 py-2 text-xs font-semibold uppercase tracking-wider rounded-lg transition-all ${
              !isRegistering ? 'bg-card text-accent shadow-sm' : 'text-text-muted hover:text-text-primary'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsRegistering(true); setLocalError(null); }}
            className={`flex-1 py-2 text-xs font-semibold uppercase tracking-wider rounded-lg transition-all ${
              isRegistering ? 'bg-card text-accent shadow-sm' : 'text-text-muted hover:text-text-primary'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Glassmorphic Auth Form */}
        <div className="glass-card p-6 md:p-8 rounded-b-xl border-b border-x border-border space-y-6">
          <div className="space-y-2">
            <h2 className="text-lg font-semibold text-text-primary">
              {isRegistering ? 'Start climbing today' : 'Welcome back'}
            </h2>
            <p className="text-xs text-text-muted">
              {isRegistering
                ? 'Sign up with your competitive programming profiles to track progress.'
                : 'Enter your credentials to access your ClimbCP analytics dashboard.'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username Field */}
            <div className="space-y-1.5">
              <label htmlFor="username-input" className="text-[10px] font-bold uppercase tracking-wider text-text-muted flex items-center gap-1">
                <User size={11} /> {isRegistering ? 'Username' : 'Username or Email'}
              </label>
              <input
                id="username-input"
                type="text"
                autoFocus={!isRegistering}
                placeholder={isRegistering ? 'e.g. john_doe' : 'Enter username or email'}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
                className="w-full bg-muted border border-border rounded-lg px-3.5 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent focus:bg-card/40 transition-all"
              />
            </div>

            {/* Email Field (Only during registration) */}
            {isRegistering && (
              <div className="space-y-1.5 animate-fade-in">
                <label htmlFor="email-input" className="text-[10px] font-bold uppercase tracking-wider text-text-muted flex items-center gap-1">
                  <Mail size={11} /> Email Address
                </label>
                <input
                  id="email-input"
                  type="email"
                  placeholder="e.g. john@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  className="w-full bg-muted border border-border rounded-lg px-3.5 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent focus:bg-card/40 transition-all"
                />
              </div>
            )}

            {/* Codeforces Handle Field (Only during registration) */}
            {isRegistering && (
              <div className="space-y-1.5 animate-fade-in">
                <label htmlFor="cf-input" className="text-[10px] font-bold uppercase tracking-wider text-text-muted flex items-center gap-1">
                  <Trophy size={11} /> Codeforces Handle
                </label>
                <input
                  id="cf-input"
                  type="text"
                  placeholder="e.g. tourist, Benq"
                  value={codeforcesHandle}
                  onChange={(e) => setCodeforcesHandle(e.target.value)}
                  disabled={loading}
                  className="w-full bg-muted border border-border rounded-lg px-3.5 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent focus:bg-card/40 transition-all font-mono"
                />
              </div>
            )}

            {/* Password Field */}
            <div className="space-y-1.5">
              <label htmlFor="password-input" className="text-[10px] font-bold uppercase tracking-wider text-text-muted flex items-center gap-1">
                <Lock size={11} /> Password
              </label>
              <input
                id="password-input"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                className="w-full bg-muted border border-border rounded-lg px-3.5 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent focus:bg-card/40 transition-all"
              />
            </div>

            {/* Confirm Password Field (Only during registration) */}
            {isRegistering && (
              <div className="space-y-1.5 animate-fade-in">
                <label htmlFor="confirm-password-input" className="text-[10px] font-bold uppercase tracking-wider text-text-muted flex items-center gap-1">
                  <Key size={11} /> Confirm Password
                </label>
                <input
                  id="confirm-password-input"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={loading}
                  className="w-full bg-muted border border-border rounded-lg px-3.5 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent focus:bg-card/40 transition-all"
                />
              </div>
            )}

            {/* Error Message */}
            {localError && (
              <div className="flex items-start gap-2.5 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs animate-fade-in">
                <AlertCircle size={14} className="shrink-0 mt-0.5" />
                <span>{localError}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-accent text-white font-semibold text-sm hover:bg-accent/90 disabled:bg-accent/40 active:translate-y-0.5 transition-all shadow-md shadow-accent/20 cursor-pointer mt-2"
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>{isRegistering ? 'Syncing profiles & creating account...' : 'Logging in...'}</span>
                </>
              ) : (
                <span>{isRegistering ? 'Register & Verify Profile' : 'Sign In'}</span>
              )}
            </button>
          </form>

          {/* Toggle Footnote */}
          <div className="text-center pt-2">
            <button
              type="button"
              onClick={handleToggleMode}
              disabled={loading}
              className="text-xs text-accent hover:text-accent/80 font-medium transition-colors cursor-pointer focus:outline-none"
            >
              {isRegistering ? 'Already have an account? Sign In' : 'Need an account? Create one'}
            </button>
          </div>
        </div>

        {/* Footnote */}
        <p className="text-center text-xs text-text-muted mt-6 tracking-wide">
          ClimbCP syncs profile data, rating logs, and contest history in real-time.
        </p>
      </div>
    </div>
  );
}
