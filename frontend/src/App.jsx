import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AnalyticsProvider, useAnalytics } from './hooks/AnalyticsContext';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import TopicAnalytics from './pages/TopicAnalytics';
import WeaknessAnalysis from './pages/WeaknessAnalysis';
import Recommendations from './pages/Recommendations';
import AiCoach from './pages/AiCoach';
import Login from './pages/Login';
import SimilarUsers from './pages/SimilarUsers';

function AppContent() {
  const { handle } = useAnalytics();

  if (!handle) {
    return <Login />;
  }

  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="/topics" element={<TopicAnalytics />} />
        <Route path="/weaknesses" element={<WeaknessAnalysis />} />
        <Route path="/recommendations" element={<Recommendations />} />
        <Route path="/ai-coach" element={<AiCoach />} />
        <Route path="/similar-users" element={<SimilarUsers />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AnalyticsProvider>
        <AppContent />
      </AnalyticsProvider>
    </BrowserRouter>
  );
}
