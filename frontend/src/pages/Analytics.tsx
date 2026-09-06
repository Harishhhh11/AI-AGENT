import { useEffect, useState } from "react";
import { getAnalyticsOverview, type AnalyticsOverview, type RankedQuestion } from "../api/analytics";

export default function Analytics() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getAnalyticsOverview()
      .then(setData)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unable to load analytics."));
  }, []);

  if (error) return <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">{error}</div>;
  if (!data) return <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">Loading analytics…</div>;

  const cards = [
    ["Conversations", data.conversations.total, `${data.conversations.active} active`],
    ["Total messages", data.messages.total, `${data.messages.average_per_conversation} per conversation`],
    ["Leads", data.leads.total, `${data.leads.qualified} qualified`],
    ["Conversion rate", `${data.conversion_rate}%`, `${data.leads.converted} converted`],
  ];

  return <div className="space-y-6">
    <header><p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Performance intelligence</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Analytics</h1><p className="mt-1 text-sm text-slate-500">Understand customer demand and where your receptionist needs better answers.</p></header>
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{cards.map(([label, value, detail]) => <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-3 text-3xl font-bold text-slate-900">{value}</p><p className="mt-2 text-xs text-slate-500">{detail}</p></div>)}</div>
    <div className="grid gap-6 lg:grid-cols-2"><QuestionList title="Popular questions" description="Most common customer questions" items={data.popular_questions} /><QuestionList title="Unanswered questions" description="Questions that need knowledge-base coverage" items={data.unanswered_questions} /></div>
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="font-bold text-slate-900">Lead funnel</h2><div className="mt-5 grid gap-4 sm:grid-cols-4">{[["New", data.leads.new], ["Qualified", data.leads.qualified], ["Converted", data.leads.converted], ["Closed conversations", data.conversations.completed]].map(([label, value]) => <div key={label} className="rounded-xl bg-slate-50 p-4"><p className="text-sm text-slate-500">{label}</p><p className="mt-1 text-2xl font-bold text-slate-900">{value}</p></div>)}</div></section>
  </div>;
}

function QuestionList({ title, description, items }: { title: string; description: string; items: RankedQuestion[] }) {
  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="font-bold text-slate-900">{title}</h2><p className="mt-1 text-sm text-slate-500">{description}</p><div className="mt-4 space-y-3">{items.map((item) => <div key={item.question} className="flex items-center justify-between gap-4 rounded-xl bg-slate-50 px-4 py-3"><span className="text-sm text-slate-700">{item.question}</span><span className="shrink-0 rounded-full bg-indigo-100 px-2.5 py-1 text-xs font-bold text-indigo-700">{item.count}</span></div>)}{items.length === 0 && <p className="rounded-xl bg-slate-50 px-4 py-5 text-sm text-slate-500">No questions recorded yet.</p>}</div></section>;
}
