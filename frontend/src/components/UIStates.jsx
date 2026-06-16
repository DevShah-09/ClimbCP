import { Loader2, AlertCircle, SearchX, Inbox } from 'lucide-react';

export function LoadingSpinner({ size = 24, message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-text-muted">
      <Loader2 size={size} className="animate-spin text-accent" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16 text-center px-4">
      <div className="p-4 rounded-full bg-red-500/10 border border-red-500/20">
        <AlertCircle size={28} className="text-red-400" />
      </div>
      <div>
        <h3 className="font-semibold text-text-primary mb-1">Something went wrong</h3>
        <p className="text-sm text-text-muted max-w-sm">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 rounded-lg bg-muted border border-border text-sm text-text-secondary hover:text-text-primary hover:border-accent/40 transition-all"
        >
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ message = 'No data available', icon: Icon = Inbox }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      <div className="p-4 rounded-full bg-muted border border-border">
        <Icon size={24} className="text-text-muted" />
      </div>
      <p className="text-sm text-text-muted">{message}</p>
    </div>
  );
}

export function NotSearchedState() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-center px-4">
      <div className="p-5 rounded-full bg-accent/10 border border-accent/20">
        <SearchX size={32} className="text-accent" />
      </div>
      <div>
        <h3 className="font-kalam font-bold text-2xl text-text-primary mb-2">Search a Handle</h3>
        <p className="text-sm text-text-muted max-w-xs">
          Enter a Codeforces handle in the search bar above to load analytics.
        </p>
      </div>
    </div>
  );
}
