import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";
import { Component, type ErrorInfo, type ReactNode } from "react";

import DashboardLayout from "./components/layout/DashboardLayout";

import Dashboard from "./pages/Dashboard";
import Leads from "./pages/Leads";
import Conversations from "./pages/Conversations";
import Knowledge from "./pages/Knowledge";
import Documents from "./pages/Documents";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat.tsx";
import PublicChat from "./pages/PublicChat";
import Agents from "./pages/Agents";
import Team from "./pages/Team";
import Settings from "./pages/Settings";
import Analytics from "./pages/Analytics";
import Integrations from "./pages/Integrations";
import NotFound from "./pages/NotFound";

function App() {

  return (
    <AppErrorBoundary>
      <BrowserRouter>

        <Routes>

        {/* LOGIN */}

        <Route
          path="/login"
          element={
            <Login />
          }
        />
        <Route path="/register" element={<Register />} />

        <Route path="/chat/:slug" element={<PublicChat />} />


        {/* DASHBOARD */}

        <Route
          element={
            <DashboardLayout />
          }
        >

          <Route
            path="/"
            element={
              <Dashboard />
            }
          />

          <Route
          path="/chat"
            element={
              <Chat />
            }
          />

          <Route path="/agents" element={<Agents />} />
          <Route path="/team" element={<Team />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/integrations" element={<Integrations />} />

          <Route
            path="/leads"
            element={
              <Leads />
            }
          />

          <Route
            path="/conversations"
            element={
              <Conversations />
            }
          />

          <Route
            path="/conversations/:id"
            element={
              <Conversations />
            }
          />

          <Route
            path="/knowledge"
            element={
              <Knowledge />
            }
          />

          <Route
            path="/documents"
            element={
              <Documents />
            }
          />

        </Route>

        <Route path="*" element={<NotFound />} />

        </Routes>

      </BrowserRouter>
    </AppErrorBoundary>
  );
}

class AppErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Frontend rendering error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="grid min-h-screen place-items-center bg-slate-950 px-6 text-center text-white">
          <div className="max-w-md">
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-indigo-300">
              Workspace unavailable
            </p>
            <h1 className="mt-4 text-4xl font-bold">The app hit an unexpected error.</h1>
            <p className="mt-4 text-sm leading-6 text-slate-300">
              Refresh the page to try again. If the problem continues, restart the frontend
              development server.
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-8 rounded-xl bg-indigo-500 px-5 py-3 text-sm font-bold transition hover:bg-indigo-400"
            >
              Refresh workspace
            </button>
          </div>
        </main>
      );
    }

    return this.props.children;
  }
}

export default App;
