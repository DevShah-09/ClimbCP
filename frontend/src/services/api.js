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

  // Phase 3 — live backend endpoint (limit: 1–30)
  getRecommendations: (handle, limit = 10) =>
    api.get(`/recommendations/${handle}`, { params: { limit } }).then(r => r.data.recommendations ?? []),
};

export const aiApi = {
  getContestReview: (handle, contestId) => 
    api.post('/ai/contest-review', { handle, contest_id: contestId }).then(r => r.data),
  getRatingLoss: (handle) => 
    api.get(`/ai/rating-loss/${handle}`).then(r => r.data),
  getBottlenecks: (handle) => 
    api.get(`/ai/bottlenecks/${handle}`).then(r => r.data),
};

export const embeddingsApi = {
  generateProblems: () => api.post('/embeddings/problems/generate').then(r => r.data),
  generateUser: (handle) => api.post(`/embeddings/users/generate/${handle}`).then(r => r.data),
};

export const conceptsApi = {
  getConcepts: (handle) => api.get(`/concepts/${handle}`).then(r => r.data),
};

export const problemsApi = {
  getSimilar: (problemId) => api.get(`/problems/${problemId}/similar`).then(r => r.data),
};

export const recommendationsApiV2 = {
  getRecommendationsV2: (handle) => api.get(`/recommendations/v2/${handle}`).then(r => r.data.recommendations ?? []),
};

export const usersApi = {
  getSimilar: (handle) => api.get(`/users/${handle}/similar`).then(r => r.data),
};

export default api;

