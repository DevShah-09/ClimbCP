import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AnalyticsProvider, useAnalytics } from './hooks/AnalyticsContext';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import TopicAnalytics from './pages/TopicAnalytics';
import WeaknessAnalysis from './pages/WeaknessAnalysis';
import Recommendations from './pages/Recommendations';
import AiCoach from './pages/AiCoach';
import Login from './pages/Login';
import { LoadingSpinner } from './components/UIStates';

function AppContent() {
  const { handle, initialized } = useAnalytics();

  if (!initialized) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoadingSpinner size={32} message="Loading your CP profile..." />
      </div>
    );
  }

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

