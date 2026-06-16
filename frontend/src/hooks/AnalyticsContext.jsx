import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { analyticsApi } from '../services/api';

const AnalyticsContext = createContext(null);

export function AnalyticsProvider({ children }) {
  const [handle, setHandle] = useState('');
  const [analytics, setAnalytics] = useState(null);
  const [ratingHistory, setRatingHistory] = useState(null);
  const [contestStats, setContestStats] = useState(null);
  const [activityStats, setActivityStats] = useState(null);
  const [topicData, setTopicData] = useState(null);
  const [weaknesses, setWeaknesses] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [initialized, setInitialized] = useState(false);

  const fetchAllData = useCallback(async (searchHandle) => {
    if (!searchHandle?.trim()) return false;
    setLoading(true);
    setError(null);
    const h = searchHandle.trim();

    try {
      const [userAnalytics, ratings, contests, activity, topics, weak, recs] = await Promise.allSettled([
        analyticsApi.getUserAnalytics(h),
        analyticsApi.getRatingHistory(h),
        analyticsApi.getContestStats(h),
        analyticsApi.getActivityStats(h),
        analyticsApi.getTopicAnalytics(h),
        analyticsApi.getWeaknesses(h),
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
      setRecommendations(recs.status === 'fulfilled' ? recs.value : null);
      
      setHandle(h);
      localStorage.setItem('climbcp_handle', h);
      return true;
    } catch (err) {
      setError(err.message || 'An unexpected error occurred');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearData = useCallback(() => {
    setHandle('');
    setAnalytics(null);
    setRatingHistory(null);
    setContestStats(null);
    setActivityStats(null);
    setTopicData(null);
    setWeaknesses(null);
    setRecommendations(null);
    setError(null);
    localStorage.removeItem('climbcp_handle');
  }, []);

  // Auto-login on mount
  useEffect(() => {
    const savedHandle = localStorage.getItem('climbcp_handle');
    if (savedHandle) {
      fetchAllData(savedHandle).finally(() => setInitialized(true));
    } else {
      setInitialized(true);
    }
  }, [fetchAllData]);

  return (
    <AnalyticsContext.Provider value={{
      handle, analytics, ratingHistory, contestStats, activityStats,
      topicData, weaknesses, recommendations, loading, error, initialized,
      fetchAllData, clearData,
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

