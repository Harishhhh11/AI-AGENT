import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createAgent, getAgents, publishAgent, unpublishAgent } from "../api/agents";
import type { Agent, AgentCreate } from "../api/agents";

const EMPTY: AgentCreate = { name: "", public_slug: "", welcome_message: "Hello! How can I help you today?", system_instructions: "" };

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [form, setForm] = useState<AgentCreate>(EMPTY);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { void getAgents().then(setAgents).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to load receptionists.")); }, []);
  const published = useMemo(() => agents.filter((agent) => agent.is_published && agent.is_active).length, [agents]);

  function setName(value: string) {
    setForm((current) => ({ ...current, name: value, public_slug: current.public_slug || value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") }));
  }
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError("");
    try { const agent = await createAgent({ ...form, name: form.name.trim(), public_slug: form.public_slug.trim(), welcome_message: form.welcome_message.trim() }); setAgents((current) => [agent, ...current]); setForm(EMPTY); setOpen(false); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to create receptionist."); }
    finally { setSaving(false); }
  }
  async function togglePublish(agent: Agent) {
    setSaving(true); setError("");
    try { const updated = agent.is_published ? await unpublishAgent(agent.id) : await publishAgent(agent.id); setAgents((items) => items.map((item) => item.id === updated.id ? updated : item)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to update receptionist."); }
    finally { setSaving(false); }
  }
  function copy(url: string) { void navigator.clipboard.writeText(url).catch(() => setError("Could not copy the link. Select and copy it manually.")); }

  return <div className="space-y-6">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Multi-company SaaS</p><h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">AI Receptionists</h1><p className="mt-1 text-sm text-slate-500">Create separate, publishable assistants with their own public URLs and knowledge.</p></div><button onClick={() => setOpen(true)} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-700">+ Create receptionist</button></div>
    <div className="grid gap-3 sm:grid-cols-3"><Metric label="Receptionists" value={agents.length} /><Metric label="Published" value={published} green /><Metric label="Private drafts" value={agents.length - published} /></div>
    {error && <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
    {open && <section className="rounded-2xl border border-indigo-100 bg-white p-5 shadow-sm sm:p-6"><div className="flex justify-between gap-4"><div><h2 className="font-bold text-slate-900">New AI receptionist</h2><p className="mt-1 text-sm text-slate-500">The public URL is permanent after creation.</p></div><button onClick={() => setOpen(false)} className="text-sm font-semibold text-slate-500">Close</button></div><form onSubmit={submit} className="mt-5 grid gap-4"><label className="block"><span className="mb-1.5 block text-sm font-semibold text-slate-700">Receptionist name</span><input required value={form.name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Admissions Assistant" className="input" /></label><label className="block"><span className="mb-1.5 block text-sm font-semibold text-slate-700">Public URL slug</span><div className="flex rounded-xl border border-slate-200 bg-slate-50 text-sm focus-within:border-indigo-400"><span className="shrink-0 px-3 py-2.5 text-slate-400">/chat/</span><input required value={form.public_slug} onChange={(e) => setForm((v) => ({ ...v, public_slug: e.target.value.toLowerCase() }))} placeholder="admissions-assistant" className="min-w-0 flex-1 bg-transparent py-2.5 pr-3 outline-none" /></div></label><label className="block"><span className="mb-1.5 block text-sm font-semibold text-slate-700">Welcome message</span><input required value={form.welcome_message} onChange={(e) => setForm((v) => ({ ...v, welcome_message: e.target.value }))} className="input" /></label><label className="block"><span className="mb-1.5 block text-sm font-semibold text-slate-700">Optional behaviour instructions</span><textarea value={form.system_instructions} onChange={(e) => setForm((v) => ({ ...v, system_instructions: e.target.value }))} rows={3} placeholder="Example: Be warm, use simple language, and offer callbacks for complex queries." className="input resize-y" /></label><div className="flex justify-end gap-2"><button type="button" onClick={() => setOpen(false)} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold">Cancel</button><button disabled={saving} className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{saving ? "Creating…" : "Create draft"}</button></div></form></section>}
    <div className="grid gap-4 lg:grid-cols-2">{agents.map((agent) => { const url = `${window.location.origin}/chat/${agent.public_slug}`; return <article key={agent.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-3"><div><span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${agent.is_published ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>{agent.is_published ? "Published" : "Draft"}</span><h2 className="mt-3 font-bold text-slate-900">{agent.name}</h2><p className="mt-1 text-sm text-slate-500">{agent.welcome_message}</p></div><button disabled={saving} onClick={() => void togglePublish(agent)} className={`rounded-xl px-3 py-2 text-xs font-semibold ${agent.is_published ? "border border-slate-200 text-slate-700" : "bg-indigo-600 text-white"}`}>{agent.is_published ? "Unpublish" : "Publish"}</button></div><div className="mt-5 rounded-xl bg-slate-50 p-3"><p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Public chat link</p><div className="mt-1 flex items-center gap-2"><code className="min-w-0 flex-1 truncate text-xs text-slate-600">{url}</code><button onClick={() => copy(url)} className="text-xs font-semibold text-indigo-700">Copy</button></div></div><div className="mt-4 flex gap-3 text-sm font-semibold text-indigo-700"><Link to={`/chat/${agent.public_slug}`} target="_blank">Preview public chat</Link><Link to="/knowledge">Manage knowledge</Link></div></article>; })}</div>
    {agents.length === 0 && <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center"><p className="font-bold text-slate-800">Create your first receptionist</p><p className="mt-2 text-sm text-slate-500">Publish it when its knowledge is ready, then share its public link.</p></div>}
  </div>;
}

function Metric({ label, value, green }: { label: string; value: number; green?: boolean }) { return <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"><p className="text-xs font-medium text-slate-500">{label}</p><p className={`mt-1 text-2xl font-bold ${green ? "text-emerald-600" : "text-slate-900"}`}>{value}</p></div>; }
