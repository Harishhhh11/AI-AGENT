import { NavLink } from "react-router-dom";

const navigation = [
  { name: "Dashboard", path: "/" },
  { name: "AI Receptionist", path: "/chat" },
  { name: "AI Receptionists", path: "/agents" },
  { name: "Leads", path: "/leads" },
  { name: "Conversations", path: "/conversations" },
  { name: "Knowledge Base", path: "/knowledge" },
  { name: "Documents", path: "/documents" },
];

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {open && <button type="button" aria-label="Close navigation" onClick={onClose} className="fixed inset-0 z-40 bg-slate-950/40 backdrop-blur-sm lg:hidden" />}
      <aside className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-slate-950 text-white shadow-2xl transition-transform duration-200 lg:static lg:z-auto lg:min-h-screen lg:w-64 lg:translate-x-0 lg:shadow-none ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex items-start justify-between px-6 py-7">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500 text-sm font-bold shadow-lg shadow-indigo-500/20">AI</div>
            <div>
              <h1 className="text-base font-bold tracking-tight">AI Receptionist</h1>
              <p className="mt-0.5 text-[11px] text-slate-400">Admin workspace</p>
            </div>
          </div>
          <button type="button" aria-label="Close navigation" onClick={onClose} className="rounded-lg px-2 py-1.5 text-xs font-semibold text-slate-400 hover:bg-white/10 hover:text-white lg:hidden">Close</button>
        </div>

        <nav className="space-y-1 px-3">
          <p className="px-4 pb-2 pt-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Workspace</p>
          {navigation.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              onClick={onClose}
              className={({ isActive }) => `group flex items-center justify-between rounded-xl px-4 py-3 text-sm font-medium transition ${isActive ? "bg-white/10 text-white shadow-inner" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}
            >
              <span>{item.name}</span>
              <span aria-hidden="true" className="text-xs text-slate-600 transition group-hover:text-slate-400">&gt;</span>
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto px-6 py-6">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs font-semibold text-white">Need to update answers?</p>
            <p className="mt-1 text-[11px] leading-5 text-slate-400">Add company information in the Knowledge Base.</p>
          </div>
        </div>
      </aside>
    </>
  );
}
