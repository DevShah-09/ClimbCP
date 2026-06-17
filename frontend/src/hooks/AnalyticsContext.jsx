import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { analyticsApi, authApi } from '../services/api';

const AnalyticsContext = createContext(null);

export function AnalyticsProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
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
      setWeaknesses(weak.status === 'fulfilled' ? weaknesses.value : null);
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

  const login = useCallback(async (username, password) => {
    setLoading(true);
    setError(null);
    try {
      const res = await authApi.login({ username, password });
      setToken(res.access_token);
      setUser(res.user);
      setHandle(res.user.codeforces_handle);
      localStorage.setItem('climbcp_token', res.access_token);
      localStorage.setItem('climbcp_handle', res.user.codeforces_handle);
      
      // Load analytics data
      await fetchAllData(res.user.codeforces_handle);
      return true;
    } catch (err) {
      setError(err.message || 'Login failed');
      return false;
    } finally {
      setLoading(false);
    }
  }, [fetchAllData]);

  const register = useCallback(async (username, email, codeforces_handle, password) => {
    setLoading(true);
    setError(null);
    try {
      // Register the user & trigger initial sync in backend
      await authApi.register({ username, email, codeforces_handle, password });
      
      // Auto login
      const success = await login(username, password);
      return success;
    } catch (err) {
      setError(err.message || 'Registration failed');
      return false;
    } finally {
      setLoading(false);
    }
  }, [login]);

  const clearData = useCallback(() => {
    setHandle('');
    setUser(null);
    setToken(null);
    setAnalytics(null);
    setRatingHistory(null);
    setContestStats(null);
    setActivityStats(null);
    setTopicData(null);
    setWeaknesses(null);
    setRecommendations(null);
    setError(null);
    localStorage.removeItem('climbcp_handle');
    localStorage.removeItem('climbcp_token');
  }, []);

  // Auto-login on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('climbcp_token');
    const loadSession = async () => {
      if (savedToken) {
        setToken(savedToken);
        try {
          const me = await authApi.getMe();
          setUser(me);
          setHandle(me.codeforces_handle);
          localStorage.setItem('climbcp_handle', me.codeforces_handle);
          await fetchAllData(me.codeforces_handle);
        } catch (err) {
          console.error("Session load failed, clearing tokens:", err);
          clearData();
        }
      }
      setInitialized(true);
    };
    loadSession();
  }, [fetchAllData, clearData]);

  return (
    <AnalyticsContext.Provider value={{
      user, token, handle, analytics, ratingHistory, contestStats, activityStats,
      topicData, weaknesses, recommendations, loading, error, initialized,
      fetchAllData, clearData, login, register
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
