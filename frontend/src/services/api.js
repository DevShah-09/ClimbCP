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
  // Mocked endpoints for Phase 2/3 features
  getTopicAnalytics: (handle) => api.get(`/topics/${handle}`).then(r => r.data).catch(() => MOCK_TOPICS),
  getWeaknesses: (handle) => api.get(`/weaknesses/${handle}`).then(r => r.data).catch(() => MOCK_WEAKNESSES),
  getRecommendations: (handle) => api.get(`/recommendations/${handle}`).then(r => r.data).catch(() => MOCK_RECOMMENDATIONS),
};

// Mock data for Phase 2/3 endpoints (not yet implemented in backend)
const MOCK_TOPICS = [
  { topic: 'Dynamic Programming', score: 72, solved: 145, accuracy: 68, strength: 'Strong' },
  { topic: 'Graphs', score: 52, solved: 89, accuracy: 55, strength: 'Moderate' },
  { topic: 'Greedy Algorithms', score: 84, solved: 210, accuracy: 79, strength: 'Expert' },
  { topic: 'Math', score: 91, solved: 312, accuracy: 88, strength: 'Expert' },
  { topic: 'Binary Search', score: 78, solved: 134, accuracy: 76, strength: 'Strong' },
  { topic: 'Trees', score: 61, solved: 98, accuracy: 62, strength: 'Moderate' },
  { topic: 'Two Pointers', score: 80, solved: 176, accuracy: 81, strength: 'Strong' },
  { topic: 'String Algorithms', score: 55, solved: 67, accuracy: 54, strength: 'Moderate' },
];

const MOCK_WEAKNESSES = [
  { topic: 'Graphs', score: 52, priority: 'High', suggestion: 'Practice BFS/DFS traversal and shortest path algorithms. Focus on Dijkstra and Bellman-Ford.' },
  { topic: 'String Algorithms', score: 55, priority: 'High', suggestion: 'Work on KMP, Z-algorithm, and suffix arrays. String hashing problems recommended.' },
  { topic: 'Trees', score: 61, priority: 'Medium', suggestion: 'Strengthen tree DP and LCA concepts. Euler tour and HLD are key advanced topics.' },
  { topic: 'Dynamic Programming', score: 72, priority: 'Low', suggestion: 'Work on bitmask DP and interval DP to push past current plateaus.' },
];

const MOCK_RECOMMENDATIONS = [
  { problem_name: 'Dijkstra\'s Shortest Path', rating: 1700, topics: ['Graphs', 'Shortest Paths'], reason: 'Targets your graph weakness.', difficulty: 'Medium' },
  { problem_name: 'KMP String Matching', rating: 1900, topics: ['String Algorithms'], reason: 'High-value string problem you haven\'t attempted.', difficulty: 'Hard' },
  { problem_name: 'Tree DP Classic', rating: 1600, topics: ['Trees', 'Dynamic Programming'], reason: 'Combines your two weaker areas.', difficulty: 'Medium' },
  { problem_name: 'Segment Tree Beats', rating: 2200, topics: ['Data Structures'], reason: 'Next-level challenge for your skill range.', difficulty: 'Expert' },
  { problem_name: 'Greedy Scheduling', rating: 1400, topics: ['Greedy Algorithms'], reason: 'Builds on your strongest topic.', difficulty: 'Easy' },
  { problem_name: 'Binary Search on Answer', rating: 1800, topics: ['Binary Search'], reason: 'Solidify a key pattern for contests.', difficulty: 'Medium' },
];

export default api;
