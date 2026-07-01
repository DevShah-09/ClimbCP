import { createContext, useContext, useState, useCallback } from 'react';
import { analyticsApi, syncApi } from '../services/api';

const AnalyticsContext = createContext(null);

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
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);

  const fetchAllData = useCallback(async (searchHandle) => {
    if (!searchHandle?.trim()) return false;
    setLoading(true);
    setError(null);
    const h = searchHandle.trim();

    try {
      const [userAnalytics, ratings, contests, activity, topics, weak, strengths, recs] = await Promise.allSettled([
        analyticsApi.getUserAnalytics(h),
        analyticsApi.getRatingHistory(h),
        analyticsApi.getContestStats(h),
        analyticsApi.getActivityStats(h),
        analyticsApi.getTopicAnalytics(h),
        analyticsApi.getWeaknesses(h),
        analyticsApi.getStrengths(h),
        analyticsApi.getRecommendations(h),
      ]);

      if (userAnalytics.status === 'rejected') {
        setError(userAnalytics.reason?.message || 'User not found');
        setLoading(false);
        return false;
      }

      setAnalytics(userAnalytics.value);
      setRatingHistory(ratings.status === 'fulfilled' ? ratings.value : []);
      setContestStats(contests.status === 'fulfilled' ? contests.value : null);
      setActivityStats(activity.status === 'fulfilled' ? activity.value : null);
      setTopicData(topics.status === 'fulfilled' ? topics.value : null);
      setWeaknesses(weak.status === 'fulfilled' ? weak.value : null);
      setStrengths(strengths.status === 'fulfilled' ? strengths.value : null);
      setRecommendations(recs.status === 'fulfilled' ? recs.value : null);

      setHandle(h);
      return true;
    } catch (err) {
      setError(err.message || 'An unexpected error occurred');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Main entry point: sync the handle with Codeforces then load all data.
   * Always fetches fresh data from CF on every call (fixes stale rating bug).
   */
  const enterHandle = useCallback(async (inputHandle) => {
    if (!inputHandle?.trim()) return false;
    const h = inputHandle.trim();
    setError(null);
    setSyncing(true);

    try {
      // Step 1: Sync with Codeforces API (creates/updates CFUser + fetches latest rating/submissions)
      await syncApi.syncHandle(h);
    } catch (err) {
      // If CF is down or handle invalid, surface the error and stop
      setError(err.message || 'Failed to sync with Codeforces. Check the handle and try again.');
      setSyncing(false);
      return false;
    } finally {
      setSyncing(false);
    }

    // Step 2: Load analytics from DB (which now has fresh data)
    return fetchAllData(h);
  }, [fetchAllData]);

  const clearData = useCallback(() => {
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
  }, []);

  return (
    <AnalyticsContext.Provider value={{
      handle, analytics, ratingHistory, contestStats, activityStats,
      topicData, weaknesses, strengths, recommendations,
      loading, syncing, error,
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
