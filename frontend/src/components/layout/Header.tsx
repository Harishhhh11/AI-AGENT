import { useMemo } from "react";

interface HeaderProps {
  onMenuClick: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {
  const user = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem("user") ?? "null") as { first_name?: string; email?: string } | null;
    } catch {
      return null;
    }
  }, []);

  function signOut() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    localStorage.removeItem("user");
    window.location.href = "/login";
  }

  const initial = (user?.first_name?.trim()?.[0] ?? "A").toUpperCase();

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
      <div className="flex h-[76px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <button type="button" aria-label="Open navigation" onClick={onMenuClick} className="rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 shadow-sm transition hover:bg-slate-50 lg:hidden">
            <span className="block h-0.5 w-4 bg-current" />
            <span className="mt-1 block h-0.5 w-4 bg-current" />
            <span className="mt-1 block h-0.5 w-4 bg-current" />
          </button>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-sm shadow-emerald-400/50" />
              <p className="truncate text-sm font-semibold text-slate-900 sm:text-base">AI Receptionist Platform</p>
            </div>
            <p className="mt-1 hidden text-xs text-slate-400 sm:block">Manage conversations, knowledge, leads and integrations from one workspace.</p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 md:flex">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> System online
          </div>
          <div className="hidden items-center gap-2 rounded-xl border border-slate-200 bg-white px-2.5 py-2 sm:flex">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-xs font-bold text-white">{initial}</div>
            <div className="max-w-[180px] text-right">
              <p className="truncate text-xs font-semibold text-slate-800">{user?.first_name ?? "Workspace admin"}</p>
              <p className="truncate text-[11px] text-slate-400">{user?.email ?? "Secure session"}</p>
            </div>
          </div>
          <button type="button" onClick={signOut} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 shadow-sm transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 sm:text-sm">Sign out</button>
        </div>
      </div>
    </header>
  );
}
