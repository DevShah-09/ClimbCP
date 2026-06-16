import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopNavbar from './TopNavbar';

export default function MainLayout() {
  return (
    <div className="min-h-screen bg-background text-text-primary relative overflow-hidden">
      {/* Ambient background glows */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        {/* Indigo/purple top-left glow */}
        <div className="absolute top-[-15%] left-[-10%] w-[600px] h-[600px] rounded-full bg-accent/10 blur-[120px] opacity-80 animate-pulse-slow" />
        {/* Pink/rose bottom-right glow */}
        <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-accent-pink/5 blur-[120px] opacity-70" />
      </div>

      {/* UI layer */}
      <div className="relative z-10 flex">
        <Sidebar />

        <div className="flex-1 ml-56 flex flex-col min-h-screen">
          <TopNavbar />

          <main className="flex-1 pt-16 p-6 overflow-y-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
