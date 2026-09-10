import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useState } from "react";

import Sidebar from "./Sidebar";
import Header from "./Header";

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { pathname } = useLocation();
  const isChatRoute = pathname === "/chat" || pathname.startsWith("/chat/agent/");
  if (!localStorage.getItem("access_token")) return <Navigate to="/login" replace />;

  return (
    <div className={`flex min-h-screen bg-[#f5f7fb] ${isChatRoute ? "h-screen overflow-hidden" : ""}`}>
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <div className="min-w-0 flex min-h-0 flex-1 flex-col">
        <Header
          onMenuClick={() => setSidebarOpen(true)}
        />
        <main className={`mx-auto w-full max-w-[1600px] p-4 sm:p-6 lg:p-8 ${isChatRoute ? "min-h-0 flex-1 overflow-hidden" : ""}`}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
