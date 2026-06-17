import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach bearer token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('climbcp_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      const message = data?.detail || `Request failed with status ${status}`;
      return Promise.reject(new Error(message));
    } else if (error.request) {
      return Promise.reject(new Error('Network error: Could not reach the server. Make sure the backend is running.'));
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (data) => api.post('/auth/register', data).then(r => r.data),
  login: (data) => api.post('/auth/login', data).then(r => r.data),
  getMe: () => api.get('/auth/me').then(r => r.data),
};

export const analyticsApi = {
  getUserAnalytics: (handle) => api.get(`/analytics/${handle}`).then(r => r.data),
  getRatingHistory: (handle) => api.get(`/ratings/${handle}`).then(r => r.data),
  getContestStats: (handle) => api.get(`/analytics/${handle}/contests`).then(r => r.data),
  getActivityStats: (handle) => api.get(`/analytics/${handle}/activity`).then(r => r.data),

  // Phase 2 — real endpoints: transform response shape to flat arrays for components
  getTopicAnalytics: (handle) =>
    api.get(`/topics/${handle}/mastery`).then(r => r.data.masteries ?? []),
  getWeaknesses: (handle) =>
    api.get(`/weaknesses/${handle}`).then(r => r.data.weaknesses ?? []),
  getStrengths: (handle) =>
    api.get(`/strengths/${handle}`).then(r => r.data.strengths ?? []),

  // Phase 3 — still mocked
  getRecommendations: (handle) =>
    api.get(`/recommendations/${handle}`).then(r => r.data).catch(() => MOCK_RECOMMENDATIONS),
};

// ── Phase 3 mock (recommendations not yet implemented) ───────────────────────
const MOCK_RECOMMENDATIONS = [
  { problem_name: "Dijkstra's Shortest Path", rating: 1700, topics: ['Graphs', 'Shortest Paths'], reason: 'Targets your graph weakness.', difficulty: 'Medium' },
  { problem_name: 'KMP String Matching', rating: 1900, topics: ['String Algorithms'], reason: "High-value string problem you haven't attempted.", difficulty: 'Hard' },
  { problem_name: 'Tree DP Classic', rating: 1600, topics: ['Trees', 'Dynamic Programming'], reason: 'Combines your two weaker areas.', difficulty: 'Medium' },
  { problem_name: 'Segment Tree Beats', rating: 2200, topics: ['Data Structures'], reason: 'Next-level challenge for your skill range.', difficulty: 'Expert' },
  { problem_name: 'Greedy Scheduling', rating: 1400, topics: ['Greedy Algorithms'], reason: 'Builds on your strongest topic.', difficulty: 'Easy' },
  { problem_name: 'Binary Search on Answer', rating: 1800, topics: ['Binary Search'], reason: 'Solidify a key pattern for contests.', difficulty: 'Medium' },
];

export default api;

