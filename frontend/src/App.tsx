import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect } from "react";
import { useAuthStore } from "./store/auth";
import AuthPage from "./pages/AuthPage";
import WorkspacePage from "./pages/WorkspacePage";

const queryClient = new QueryClient();

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  return token ? <>{children}</> : <Navigate to="/auth" replace />;
}

function AuthRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  return token ? <Navigate to="/" replace /> : <>{children}</>;
}

function AppInit({ children }: { children: React.ReactNode }) {
  const initialize = useAuthStore((s) => s.initialize);
  useEffect(() => { initialize(); }, [initialize]);
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppInit>
          <Routes>
            <Route path="/auth" element={<AuthRoute><AuthPage /></AuthRoute>} />
            <Route path="/" element={<ProtectedRoute><WorkspacePage /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppInit>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
