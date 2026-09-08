import { BrowserRouter, Routes, Route } from "react-router-dom";
import DashboardLayout from "./components/layout/DashboardLayout";
import Dashboard from "./pages/Dashboard";
import Leads from "./pages/Leads";
import Conversations from "./pages/Conversations";
import Knowledge from "./pages/Knowledge";
import Documents from "./pages/Documents";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat.tsx";
import ChatV2 from "./pages/ChatV2";
import PublicChat from "./pages/PublicChat";
import Agents from "./pages/Agents";
import Team from "./pages/Team";
import Settings from "./pages/Settings";
import Analytics from "./pages/Analytics";
import Integrations from "./pages/Integrations";

export default function App() {
  return <BrowserRouter><Routes>
    <Route path="/login" element={<Login />} />
    <Route path="/register" element={<Register />} />
    <Route path="/chat/:slug" element={<PublicChat />} />
    <Route element={<DashboardLayout />}>
      <Route path="/" element={<Dashboard />} />
      <Route path="/chat" element={<ChatV2 />} />
      <Route path="/chat/agent/:agentId" element={<ChatV2 />} />
      <Route path="/chat-classic" element={<Chat />} />
      <Route path="/agents" element={<Agents />} />
      <Route path="/team" element={<Team />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="/analytics" element={<Analytics />} />
      <Route path="/integrations" element={<Integrations />} />
      <Route path="/leads" element={<Leads />} />
      <Route path="/conversations" element={<Conversations />} />
      <Route path="/conversations/:id" element={<Conversations />} />
      <Route path="/knowledge" element={<Knowledge />} />
      <Route path="/documents" element={<Documents />} />
    </Route>
  </Routes></BrowserRouter>;
}
