import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createAgent, getAgents, publishAgent, unpublishAgent } from "../api/agents";
import type { Agent, AgentCreate } from "../api/agents";
import PageHeader from "../components/common/PageHeader";
import StatusBadge from "../components/common/StatusBadge";
import EmptyState from "../components/common/EmptyState";

const EMPTY: AgentCreate = {
  name: "",
  public_slug: "",
  welcome_message: "Hello! How can I help you today?",
  system_instructions: "",
};

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [form, setForm] = useState<AgentCreate>(EMPTY);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadAgents() {
    setError("");
    const data = await getAgents();
    setAgents(data);
  }

  useEffect(() => {
    let mounted = true;
    void getAgents()
      .then((data) => {
        if (mounted) setAgents(data);
      })
      .catch((reason) => {
        if (mounted) setError(reason instanceof Error ? reason.message : "Unable to load receptionists.");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => { mounted = false; };
  }, []);

  const published = useMemo(() => agents.filter((agent) => agent.is_published && agent.is_active).length, [agents]);

  function setName(value: string) {
    setForm((current) => ({
      ...current,
      name: value,
      public_slug: current.public_slug || value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, ""),
    }));
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const agent = await createAgent({
        ...form,
        name: form.name.trim(),
        public_slug: form.public_slug.trim(),
        welcome_message: form.welcome_message.trim(),
      });
      setAgents((current) => [agent, ...current]);
      setForm(EMPTY);
      setOpen(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create receptionist.");
    } finally {
      setSaving(false);
    }
  }

  async function togglePublish(agent: Agent) {
    setSaving(true);
    setError("");
    try {
      const updated = agent.is_published ? await unpublishAgent(agent.id) : await publishAgent(agent.id);
      setAgents((items) => items.map((item) => item.id === updated.id ? updated : item));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to update receptionist.");
    } finally {
      setSaving(false);
    }
  }

  async function copy(url: string) {
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      setError("Could not copy the link. Select and copy it manually.");
    }
  }

  async function refresh() {
    setLoading(true);
    try {
      await loadAgents();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to refresh receptionists.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Multi-agent workspace"
        title="AI Receptionists"
        description="Create, configure, publish and test dedicated customer-facing assistants without mixing their knowledge boundaries."
        actions={(
          <>
            <button type="button" onClick={() => void refresh()} disabled={loading} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm hover:border-indigo-200 hover:text-indigo-700 disabled:opacity-50">Refresh</button>
            <button type="button" onClick={() => setOpen(true)} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-700">+ Create receptionist</button>
          </>
        )}
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Metric label="Receptionists" value={agents.length} />
        <Metric label="Published" value={published} green />
        <Metric label="Drafts / inactive" value={Math.max(0, agents.length - published)} />
      </div>

      {error && <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">{error}</div>}

      {open && (
        <section className="rounded-3xl border border-indigo-100 bg-white p-5 shadow-xl shadow-indigo-900/5 sm:p-7">
          <div className="flex items-start justify-between gap-4">
            <div><h2 className="text-lg font-bold text-slate-950">Create a receptionist</h2><p className="mt-1 text-sm text-slate-500">Start as a draft, add knowledge, test it, then publish the public URL.</p></div>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg px-2 py-1 text-sm text-slate-400 hover:bg-slate-100">Close</button>
          </div>
          <form onSubmit={submit} className="mt-6 grid gap-4">
            <label><span className="mb-1.5 block text-sm font-semibold text-slate-700">Receptionist name</span><input required value={form.name} onChange={(e) => setName(e.target.value)} placeholder="Admissions Assistant" className="input" /></label>
            <label><span className="mb-1.5 block text-sm font-semibold text-slate-700">Public URL slug</span><div className="flex overflow-hidden rounded-xl border border-slate-200 bg-slate-50 focus-within:border-indigo-400"><span className="px-3 py-2.5 text-sm text-slate-400">/chat/</span><input required value={form.public_slug} onChange={(e) => setForm((v) => ({ ...v, public_slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-") }))} className="min-w-0 flex-1 bg-transparent py-2.5 pr-3 text-sm outline-none" /></div></label>
            <label><span className="mb-1.5 block text-sm font-semibold text-slate-700">Welcome message</span><input required value={form.welcome_message} onChange={(e) => setForm((v) => ({ ...v, welcome_message: e.target.value }))} className="input" /></label>
            <label><span className="mb-1.5 block text-sm font-semibold text-slate-700">Behaviour instructions</span><textarea value={form.system_instructions} onChange={(e) => setForm((v) => ({ ...v, system_instructions: e.target.value }))} rows={4} placeholder="Be warm, concise, helpful and offer a callback when needed." className="input resize-y" /></label>
            <div className="flex justify-end gap-2"><button type="button" onClick={() => setOpen(false)} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700">Cancel</button><button disabled={saving} className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{saving ? "Creating…" : "Create draft"}</button></div>
          </form>
        </section>
      )}

      {loading ? (
        <div className="grid gap-4 lg:grid-cols-2"><Skeleton /><Skeleton /></div>
      ) : agents.length === 0 ? (
        <div className="card"><EmptyState title="No receptionists yet" description="Create your first AI receptionist, add verified knowledge, test the experience, and publish when ready." action={{ label: "Create receptionist", onClick: () => setOpen(true) }} /></div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {agents.map((agent) => {
            const url = `${window.location.origin}/chat/${agent.public_slug}`;
            return (
              <article key={agent.id} className="card overflow-hidden p-5 sm:p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0"><StatusBadge label={agent.is_published ? "Published" : "Draft"} tone={agent.is_published ? "green" : "amber"} /><h2 className="mt-3 truncate text-lg font-bold text-slate-950">{agent.name}</h2><p className="mt-1 text-sm leading-6 text-slate-500">{agent.welcome_message}</p></div>
                  <button type="button" disabled={saving} onClick={() => void togglePublish(agent)} className={`shrink-0 rounded-xl px-3 py-2 text-xs font-semibold ${agent.is_published ? "border border-slate-200 text-slate-700 hover:bg-slate-50" : "bg-indigo-600 text-white hover:bg-indigo-700"}`}>{agent.is_published ? "Unpublish" : "Publish"}</button>
                </div>
                <div className="mt-5 rounded-2xl bg-slate-50 p-4"><p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Public chat link</p><div className="mt-2 flex items-center gap-2"><code className="min-w-0 flex-1 truncate text-xs text-slate-600">{url}</code><button type="button" onClick={() => void copy(url)} className="text-xs font-semibold text-indigo-700 hover:text-indigo-800">Copy</button></div></div>
                <div className="mt-5 flex flex-wrap gap-x-4 gap-y-2 text-sm font-semibold text-indigo-700"><Link to={`/chat/${agent.public_slug}`} target="_blank" rel="noreferrer">Preview public chat →</Link><Link to="/chat">Open tester →</Link><Link to="/knowledge">Manage knowledge →</Link></div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Metric({ label, value, green }: { label: string; value: number; green?: boolean }) {
  return <div className="card p-5"><p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">{label}</p><p className={`mt-2 text-2xl font-bold ${green ? "text-emerald-600" : "text-slate-950"}`}>{value}</p></div>;
}

function Skeleton() { return <div className="card h-52 animate-pulse bg-slate-100" aria-hidden="true" />; }
