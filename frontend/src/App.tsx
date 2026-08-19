import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import DashboardLayout from "./components/layout/DashboardLayout";

import Dashboard from "./pages/Dashboard";
import Leads from "./pages/Leads";
import Conversations from "./pages/Conversations";
import Knowledge from "./pages/Knowledge";
import Documents from "./pages/Documents";
import Login from "./pages/Login";
import Chat from "./pages/Chat.tsx";
import PublicChat from "./pages/PublicChat";
import Agents from "./pages/Agents";

function App() {

  return (
    <BrowserRouter>

      <Routes>

        {/* LOGIN */}

        <Route
          path="/login"
          element={
            <Login />
          }
        />

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

      </Routes>

    </BrowserRouter>
  );
}


export default App;
