import { HashRouter, Routes, Route, NavLink, Navigate } from "react-router-dom";
import AnalyzePage from "./pages/AnalyzePage";
import DashboardPage from "./pages/DashboardPage";
import HistoryPage from "./pages/HistoryPage";
import AuthPage from "./pages/AuthPage";
import { ShieldCheck, ScanSearch, BarChart3, History } from "lucide-react";
import { AuthProvider, useAuth } from "./AuthContext";

function Nav() {
  const { user, signOut } = useAuth();

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
      isActive
        ? "bg-indigo-600 text-white"
        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
    }`;

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="text-indigo-400" size={24} />
          <span className="font-bold text-lg tracking-tight">
            ScamShield AI
          </span>
        </div>

        <nav className="flex items-center gap-1">
          <NavLink to="/" end className={linkClass}>
            <ScanSearch size={16} /> Analyze
          </NavLink>

          <NavLink to="/dashboard" className={linkClass}>
            <BarChart3 size={16} /> Dashboard
          </NavLink>

          <NavLink to="/history" className={linkClass}>
            <History size={16} /> History
          </NavLink>

          <button
            onClick={signOut}
            className="ml-2 px-4 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            Sign out
          </button>
        </nav>

        {user && (
          <span className="hidden lg:block ml-3 text-xs text-slate-500 max-w-[180px] truncate">
            {user.email}
          </span>
        )}
      </div>
    </header>
  );
}

function ProtectedApp() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center">
        <div className="text-slate-400">Loading ScamShield...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-[#0a0e17]">
      <Nav />

      <Routes>
        <Route path="/" element={<AnalyzePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <HashRouter>
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          <Route path="/*" element={<ProtectedApp />} />
        </Routes>
      </HashRouter>
    </AuthProvider>
  );
}