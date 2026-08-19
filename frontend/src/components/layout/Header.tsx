interface HeaderProps {
  onMenuClick: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {
  function signOut() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    window.location.href = "/login";
  }

  return (
    <header className="sticky top-0 z-30 flex h-[72px] items-center justify-between border-b border-slate-200/80 bg-white/90 px-4 backdrop-blur-xl sm:px-6 lg:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <button type="button" aria-label="Open navigation" onClick={onMenuClick} className="rounded-lg px-2.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 lg:hidden">
          Menu
        </button>
        <div className="min-w-0">
          <h2 className="truncate text-sm font-semibold text-slate-900 sm:text-base">AI Receptionist Platform</h2>
          <p className="hidden text-xs text-slate-400 sm:block">Intelligent customer operations</p>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <div className="hidden items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 sm:flex">
          <span className="h-2 w-2 rounded-full bg-emerald-500" /> System online
        </div>
        <button type="button" onClick={signOut} className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 sm:text-sm">
          Sign out
        </button>
      </div>
    </header>
  );
}
