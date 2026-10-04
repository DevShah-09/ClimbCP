import { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { analyticsApi, syncApi } from '../services/api';

const AnalyticsContext = createContext(null);
const HANDLE_KEY = 'climbcp.handle';

function savedHandle() {
  try { return localStorage.getItem(HANDLE_KEY) || ''; } catch { return ''; }
}
function rememberHandle(handle) {
  try {
    if (handle) localStorage.setItem(HANDLE_KEY, handle);
    else localStorage.removeItem(HANDLE_KEY);
  } catch { /* Profiles still work when browser storage is unavailable. */ }
}

export function AnalyticsProvider({ children }) {
  const [handle, setHandle] = useState('');
  const [analytics, setAnalytics] = useState(null);
  const [ratingHistory, setRatingHistory] = useState(null);
  const [contestStats, setContestStats] = useState(null);
  const [activityStats, setActivityStats] = useState(null);
  const [topicData, setTopicData] = useState(null);
  const [weaknesses, setWeaknesses] = useState(null);
  const [strengths, setStrengths] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);
  const [detailError, setDetailError] = useState(null);
  const [lastSyncedAt, setLastSyncedAt] = useState(null);
  const generation = useRef(0);
  const inFlight = useRef(null);
  const restored = useRef(false);

  const fetchAllData = useCallback(async (h, requestId = generation.current) => {
    setLoading(true);
    try {
      // Dashboard data is required; never present a partial snapshot as current.
      const [summary, ratings, contests, activity] = await Promise.all([
        analyticsApi.getUserAnalytics(h), analyticsApi.getRatingHistory(h),
        analyticsApi.getContestStats(h), analyticsApi.getActivityStats(h),
      ]);
      if (requestId !== generation.current) return false;
      setAnalytics(summary);
      setRatingHistory(ratings);
      setContestStats(contests);
      setActivityStats(activity);
      setHandle(summary.handle || h);
      rememberHandle(summary.handle || h);
      setLoading(false);
      setDetailsLoading(true);

      // Load insights separately. Recommendations are fetched on their own page.
      void Promise.allSettled([
        analyticsApi.getTopicAnalytics(h), analyticsApi.getWeaknesses(h),
        analyticsApi.getStrengths(h),
      ]).then(results => {
        if (requestId !== generation.current) return;
        const setters = [setTopicData, setWeaknesses, setStrengths];
        results.forEach((result, i) => setters[i](result.status === 'fulfilled' ? result.value : null));
        if (results.some(result => result.status === 'rejected')) {
          setDetailError('Some topic data could not be loaded. Refresh to retry.');
        }
        setDetailsLoading(false);
      });
      return true;
    } catch (err) {
      if (requestId === generation.current) setError(err.message || 'Unable to load profile. Please retry.');
      return false;
    } finally {
      if (requestId === generation.current) setLoading(false);
    }
  }, []);

  const enterHandle = useCallback((inputHandle) => {
    const h = inputHandle?.trim();
    if (!h) return Promise.resolve(false);
    if (inFlight.current) return inFlight.current;
    const requestId = ++generation.current;
    setError(null);
    setDetailError(null);
    setSyncing(true);
    setDetailsLoading(false);
    setTopicData(null);
    setWeaknesses(null);
    setStrengths(null);
    setRecommendations(null);
    const request = (async () => {
      try {
        // Every entry, including automatic restore, gets fresh profile/contest/submission data.
        const result = await syncApi.syncHandle(h);
        if (requestId !== generation.current) return false;
        const loaded = await fetchAllData(result.handle || h, requestId);
        if (loaded && requestId === generation.current) setLastSyncedAt(result.last_synced_at || null);
        return loaded;
      } catch (err) {
        if (requestId === generation.current) setError(err.message || 'Unable to refresh Codeforces data. Please retry.');
        return false;
      } finally {
        if (requestId === generation.current) {
          setSyncing(false);
          inFlight.current = null;
        }
      }
    })();
    inFlight.current = request;
    return request;
  }, [fetchAllData]);

  useEffect(() => {
    // StrictMode effect replay must not start a second synchronization.
    if (restored.current) return;
    restored.current = true;
    const previous = savedHandle();
    if (previous) void enterHandle(previous);
  }, [enterHandle]);

  const clearData = useCallback(() => {
    ++generation.current; // Ignore responses from the previous profile after logout.
    inFlight.current = null;
    rememberHandle('');
    setHandle('');
    setAnalytics(null);
    setRatingHistory(null);
    setContestStats(null);
    setActivityStats(null);
    setTopicData(null);
    setWeaknesses(null);
    setStrengths(null);
    setRecommendations(null);
    setError(null);
    setDetailError(null);
    setLastSyncedAt(null);
    setLoading(false);
    setDetailsLoading(false);
    setSyncing(false);
  }, []);

  return (
    <AnalyticsContext.Provider value={{
      handle, analytics, ratingHistory, contestStats, activityStats,
      topicData, weaknesses, strengths, recommendations,
      loading, detailsLoading, syncing, error, detailError, lastSyncedAt,
      enterHandle, fetchAllData, clearData,
    }}>
      {children}
    </AnalyticsContext.Provider>
  );
}

export function useAnalytics() {
  const ctx = useContext(AnalyticsContext);
  if (!ctx) throw new Error('useAnalytics must be used within AnalyticsProvider');
  return ctx;
}
