import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getLeads, type Lead } from "../api/leads";
import { getConversations, type Conversation } from "../api/conversations";
import { getKnowledge, type KnowledgeItem } from "../api/knowledge";
import PageHeader from "../components/common/PageHeader";
import StatusBadge from "../components/common/StatusBadge";

function formatDate(value: string | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
}

export default function Dashboard() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    Promise.all([getLeads(), getConversations(), getKnowledge()])
      .then(([leadsData, conversationData, knowledgeData]) => {
        if (!mounted) return;
        setLeads(leadsData);
        setConversations(conversationData);
        setKnowledge(knowledgeData);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : "Failed to load workspace data.");
      })
      .finally(() => mounted && setLoading(false));

    return () => {
      mounted = false;
    };
  }, [refreshToken]);

  const recentLeads = useMemo(() => [...leads].sort((a, b) => b.id - a.id).slice(0, 5), [leads]);
  const recentConversations = useMemo(() => [...conversations].sort((a, b) => b.id - a.id).slice(0, 5), [conversations]);
  const activeConversations = conversations.filter((item) => item.status === "active").length;
  const newLeads = leads.filter((item) => item.status === "new").length;

  const cards = [
    { label: "Total leads", value: leads.length, helper: `${newLeads} new`, href: "/leads", icon: "↗" },
    { label: "Conversations", value: conversations.length, helper: `${activeConversations} active now`, href: "/conversations", icon: "◌" },
    { label: "Knowledge items", value: knowledge.length, helper: "Verified company context", href: "/knowledge", icon: "✦" },
    { label: "AI status", value: "Online", helper: "Receptionist service", href: "/agents", icon: "✓" },
  ];

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Workspace overview"
        title="Good to see you."
        description="Monitor the AI receptionist, review customer activity, and keep the knowledge layer ready for every conversation."
        actions={(
          <>
            <button type="button" onClick={() => setRefreshToken((value) => value + 1)} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-indigo-200 hover:text-indigo-700">
              <span className={loading ? "pulse-soft" : ""}>↻</span> Refresh
            </button>
            <Link to="/chat" className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-indigo-600/20 transition hover:bg-indigo-700">Test receptionist <span aria-hidden="true">→</span></Link>
          </>
        )}
      />

      {error && <div className="rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700"><p className="font-semibold">Some workspace data could not be loaded.</p><p className="mt-1 text-rose-600">{error}</p></div>}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <Link key={card.label} to={card.href} className="group card block p-5 transition hover:-translate-y-0.5 hover:shadow-xl sm:p-6">
            <div className="flex items-start justify-between gap-4"><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-sm font-bold text-indigo-600">{card.icon}</div><span className="text-slate-300 transition group-hover:text-indigo-500">→</span></div>
            <p className="mt-5 text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">{card.label}</p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">{loading ? "…" : card.value}</p>
            <p className="mt-2 text-xs text-slate-500">{loading ? "Refreshing workspace" : card.helper}</p>
          </Link>
        ))}
      </section>

      <section className="overflow-hidden rounded-3xl bg-slate-950 p-6 text-white shadow-xl shadow-slate-900/10 sm:p-8">
        <div className="flex flex-col gap-7 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-2xl"><StatusBadge label="AI layer operational" tone="green" /><h2 className="mt-4 text-2xl font-bold tracking-tight sm:text-3xl">Build trust into every answer.</h2><p className="mt-3 text-sm leading-6 text-slate-300">The receptionist uses verified business knowledge, conversation context, and structured lead capture instead of inventing company facts.</p></div>
          <div className="grid w-full max-w-xl gap-3 sm:grid-cols-3">
            {[["Knowledge", `${knowledge.length}`, "items loaded"], ["Active chats", `${activeConversations}`, "right now"], ["New leads", `${newLeads}`, "need attention"]].map(([label, value, helper]) => <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-4"><p className="text-xs text-slate-400">{label}</p><p className="mt-2 text-2xl font-bold">{loading ? "…" : value}</p><p className="mt-1 text-[11px] text-slate-500">{helper}</p></div>)}
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="card overflow-hidden"><div className="flex items-center justify-between border-b border-slate-100 px-5 py-5 sm:px-6"><div><h2 className="font-semibold text-slate-950">Recent leads</h2><p className="mt-1 text-xs text-slate-500">Latest customer opportunities captured by the receptionist.</p></div><Link to="/leads" className="text-xs font-semibold text-indigo-600 hover:text-indigo-700">View all</Link></div><div className="divide-y divide-slate-100">{loading && <div className="px-6 py-10 text-center text-sm text-slate-400">Loading leads…</div>}{!loading && recentLeads.length === 0 && <div className="px-6 py-10 text-center text-sm text-slate-400">No leads yet. Start a test conversation to capture one.</div>}{!loading && recentLeads.map((lead) => <div key={lead.id} className="flex items-center justify-between gap-4 px-5 py-4 sm:px-6"><div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-900">{lead.name || lead.email || lead.phone || "Unnamed lead"}</p><p className="mt-1 truncate text-xs text-slate-500">{lead.interest || "No interest specified"}</p></div><StatusBadge label={lead.status} tone={lead.status === "new" ? "blue" : "slate"} /></div>)}</div></div>

        <div className="card overflow-hidden"><div className="flex items-center justify-between border-b border-slate-100 px-5 py-5 sm:px-6"><div><h2 className="font-semibold text-slate-950">Recent conversations</h2><p className="mt-1 text-xs text-slate-500">Latest sessions across your AI receptionist workspace.</p></div><Link to="/conversations" className="text-xs font-semibold text-indigo-600 hover:text-indigo-700">View all</Link></div><div className="divide-y divide-slate-100">{loading && <div className="px-6 py-10 text-center text-sm text-slate-400">Loading conversations…</div>}{!loading && recentConversations.length === 0 && <div className="px-6 py-10 text-center text-sm text-slate-400">No conversations yet.</div>}{!loading && recentConversations.map((conversation) => <div key={conversation.id} className="flex items-center justify-between gap-4 px-5 py-4 sm:px-6"><div className="min-w-0"><p className="text-sm font-semibold text-slate-900">Conversation #{conversation.id}</p><p className="mt-1 text-xs text-slate-500">Created {formatDate(conversation.created_at)}</p></div><StatusBadge label={conversation.status} tone={conversation.status === "active" ? "green" : "slate"} /></div>)}</div></div>
      </section>
    </div>
  );
}
