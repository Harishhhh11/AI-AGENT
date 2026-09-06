import { useEffect, useState } from "react";
import { getIntegrations, type IntegrationSummary } from "../api/integrations";

export default function Integrations() {
  const [items, setItems] = useState<IntegrationSummary[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getIntegrations()
      .then((response) => setItems(response.integrations))
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unable to load integrations."));
  }, []);

  return <div className="space-y-6">
    <header><p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Connected workflows</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Integrations</h1><p className="mt-1 max-w-2xl text-sm text-slate-500">Connect the channels and business systems that help your receptionist serve customers and move leads forward.</p></header>
    {error && <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">{error}</div>}
    <div className="grid gap-5 lg:grid-cols-2">{items.map((item) => <article key={item.key} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{item.category}</p><h2 className="mt-1 text-lg font-bold text-slate-900">{item.name}</h2></div><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${item.status === "configured" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{item.status === "configured" ? "Configured" : "Available"}</span></div><p className="mt-3 text-sm leading-6 text-slate-600">{item.description}</p><div className="mt-4 flex flex-wrap gap-2">{item.capabilities.map((capability) => <span key={capability} className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700">{capability.replace("_", " ")}</span>)}</div><p className="mt-4 border-t border-slate-100 pt-4 text-xs text-slate-500">{item.setup_hint}</p></article>)}</div>
  </div>;
}
