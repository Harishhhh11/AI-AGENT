import { NavLink } from "react-router-dom";

const sections = [
  {
    label: "Overview",
    items: [
      { name: "Dashboard", path: "/", icon: "⌂" },
      { name: "Your Receptionists", path: "/agents", icon: "◈" },
    ],
  },
  {
    label: "Customer operations",
    items: [
      { name: "Leads", path: "/leads", icon: "↗" },
      { name: "Conversations", path: "/conversations", icon: "◌" },
    ],
  },
  {
    label: "Knowledge & setup",
    items: [
      { name: "Knowledge Base", path: "/knowledge", icon: "▤" },
      { name: "Documents", path: "/documents", icon: "□" },
      { name: "Analytics", path: "/analytics", icon: "▥" },
      { name: "Integrations", path: "/integrations", icon: "⌘" },
      { name: "Team", path: "/team", icon: "◎" },
      { name: "Settings", path: "/settings", icon: "⚙" },
    ],
  },
];

interface SidebarProps { open: boolean; onClose: () => void; }

export default function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {open && <button type="button" aria-label="Close navigation" onClick={onClose} className="fixed inset-0 z-40 bg-slate-950/40 backdrop-blur-sm lg:hidden" />}
      <aside className={`fixed inset-y-0 left-0 z-50 flex w-[280px] flex-col border-r border-white/10 bg-slate-950 text-white shadow-2xl transition-transform duration-200 lg:static lg:z-auto lg:min-h-screen lg:w-64 lg:translate-x-0 lg:shadow-none ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="border-b border-white/10 px-5 py-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500 text-sm font-black shadow-lg shadow-indigo-500/20">AI</div>
            <div className="min-w-0">
              <h1 className="truncate text-sm font-bold tracking-tight">AI Receptionist Platform</h1>
              <p className="mt-0.5 text-[11px] text-slate-400">Intelligent customer operations</p>
            </div>
          </div>
        </div>
        <nav className="app-scrollbar flex-1 overflow-y-auto px-3 py-5">
          {sections.map((section) => (
            <div key={section.label} className="mb-6 last:mb-0">
              <p className="px-3 pb-2 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">{section.label}</p>
              <div className="space-y-1">
                {section.items.map((item) => (
                  <NavLink key={item.path} to={item.path} end={item.path === "/"} onClick={onClose} className={({ isActive }) => `group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${isActive ? "bg-white/10 text-white shadow-inner" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}>
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white/5 text-xs text-slate-400 group-hover:text-slate-200">{item.icon}</span>
                    <span className="min-w-0 flex-1 truncate">{item.name}</span>
                    <span aria-hidden="true" className="text-xs text-slate-600 transition group-hover:text-slate-400">›</span>
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>
        <div className="px-4 pb-4">
          <div className="rounded-2xl border border-indigo-400/20 bg-indigo-500/10 p-4">
            <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-400" /><p className="text-xs font-semibold text-white">Receptionist service online</p></div>
            <p className="mt-2 text-[11px] leading-5 text-slate-400">Keep each receptionist connected only to the knowledge selected for it.</p>
            <NavLink to="/agents" onClick={onClose} className="mt-3 inline-flex text-[11px] font-semibold text-indigo-300 hover:text-white">Manage receptionists →</NavLink>
          </div>
        </div>
      </aside>
    </>
  );
}
