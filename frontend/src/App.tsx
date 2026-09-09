import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { ScenarioListPage } from "./pages/ScenarioListPage";
import { ScenarioEditPage } from "./pages/ScenarioEditPage";
import { ScenarioResultsPage } from "./pages/ScenarioResultsPage";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="page">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route
        path="/scenarios"
        element={
          <ProtectedRoute>
            <ScenarioListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/scenarios/:id/edit"
        element={
          <ProtectedRoute>
            <ScenarioEditPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/scenarios/:id"
        element={
          <ProtectedRoute>
            <ScenarioResultsPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
