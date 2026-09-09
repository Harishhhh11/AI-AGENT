import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";

import { createAgent, deleteAgent, getAgent, getAgents, publishAgent, updateAgent } from "../api/agents";
import type { Agent, AgentCreate } from "../api/agents";
import { getKnowledge } from "../api/knowledge";
import type { KnowledgeItem } from "../api/knowledge";

const DEFAULT_FORM: AgentCreate = {
  name: "",
  public_slug: "",
  welcome_message: "Hello! How can I help you today?",
  system_instructions: "",
  knowledge_item_ids: [],
};

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([]);
  const [form, setForm] = useState<AgentCreate>(DEFAULT_FORM);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [selectedForEdit, setSelectedForEdit] = useState<Agent | null>(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [agentData, knowledgeData] = await Promise.all([getAgents(), getKnowledge(undefined, "all")]);
      setAgents(agentData);
      setKnowledge(knowledgeData);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load your receptionists.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);

  const availableKnowledge = useMemo(
    () => knowledge.filter((item) => item.is_active && (item.agent_id == null || item.agent_id === selectedForEdit?.id)),
    [knowledge, selectedForEdit],
  );

  function slugify(value: string) {
    return value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 100);
  }

  function openCreate() {
    setSelectedForEdit(null);
    setForm({ ...DEFAULT_FORM });
    setOpen(true);
    setError("");
    setSuccess("");
  }

  function openEdit(agent: Agent) {
    setSelectedForEdit(agent);
    setForm({
      name: agent.name,
      public_slug: agent.public_slug,
      welcome_message: agent.welcome_message,
      system_instructions: "",
      knowledge_item_ids: agent.knowledge_item_ids ?? [],
    });
    setOpen(true);
    setError("");
    setSuccess("");
  }

  function toggleKnowledge(id: number) {
    setForm((current) => ({
      ...current,
      knowledge_item_ids: current.knowledge_item_ids?.includes(id)
        ? current.knowledge_item_ids.filter((value) => value !== id)
        : [...(current.knowledge_item_ids ?? []), id],
    }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    const name = form.name.trim();
    const publicSlug = slugify(form.public_slug || name);
    const welcome = form.welcome_message.trim() || DEFAULT_FORM.welcome_message;
    if (!name || name.length < 2) { setError("Enter a receptionist name."); return; }
    if (!publicSlug || publicSlug.length < 3) { setError("Enter a valid public URL slug."); return; }

    setSaving(true);
    setError("");
    setSuccess("");
    try {
      if (selectedForEdit) {
        const updated = await updateAgent(selectedForEdit.id, {
          name,
          welcome_message: welcome,
          system_instructions: form.system_instructions?.trim() || null,
          knowledge_item_ids: form.knowledge_item_ids ?? [],
        });
        setAgents((current) => current.map((agent) => agent.id === updated.id ? updated : agent));
        setSuccess("Receptionist updated successfully.");
      } else {
        const created = await createAgent({
          name,
          public_slug: publicSlug,
          welcome_message: welcome,
          system_instructions: form.system_instructions?.trim() || null,
          knowledge_item_ids: form.knowledge_item_ids ?? [],
        });
        setAgents((current) => [created, ...current]);
        setSuccess("Receptionist created with the selected knowledge.");
      }
      setOpen(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save this receptionist.");
    } finally {
      setSaving(false);
    }
  }

  async function togglePublish(agent: Agent) {
    if (saving) return;
    setSaving(true); setError(""); setSuccess("");
    try {
      const updated = await publishAgent(agent.id, !agent.is_published);
      setAgents((current) => current.map((item) => item.id === updated.id ? updated : item));
      setSuccess(updated.is_published ? "Public chat is now live." : "Public chat has been unpublished.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to change public status.");
    } finally {
      setSaving(false);
    }
  }

  async function remove(agent: Agent) {
    if (saving || !window.confirm(`Delete "${agent.name}"? This cannot be undone.`)) return;
    setSaving(true); setError(""); setSuccess("");
    try {
      await deleteAgent(agent.id);
      setAgents((current) => current.filter((item) => item.id !== agent.id));
      setSuccess("Receptionist deleted.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to delete this receptionist.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-indigo-600">AI receptionists</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Your Receptionists</h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-500">Create focused receptionists, attach the exact verified knowledge they are allowed to use, and test them before publishing.</p>
        </div>
        <button type="button" onClick={openCreate} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-700">+ Create receptionist</button>
      </div>

      {error && <div role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{error}</div>}
      {success && <div role="status" className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">{success}</div>}

      {open && <section className="rounded-3xl border border-indigo-100 bg-white p-5 shadow-xl sm:p-6">
        <div className="flex items-start justify-between gap-4">
          <div><p className="text-xs font-bold uppercase tracking-[0.16em] text-indigo-600">{selectedForEdit ? "Edit receptionist" : "New receptionist"}</p><h2 className="mt-1 text-lg font-bold text-slate-900">Configure AI behavior and knowledge</h2><p className="mt-1 text-sm text-slate-500">Selected knowledge is persisted on the server and used only by this receptionist.</p></div>
          <button type="button" onClick={() => setOpen(false)} className="rounded-lg px-2 py-1 text-sm text-slate-500">Close</button>
        </div>
        <form onSubmit={submit} className="mt-6 space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block"><span className="mb-1.5 block text-sm font-semibold text-slate-700">Name</span><input required value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} onBlur={() => !selectedForEdit && form.name && !form.public_slug && setForm((current) => ({ ...current, public_slug: slugify(form.name) }))} className="input" placeholder="e.g. Course Admissions Receptionist" /></label>
            {!selectedForEdit && <label className="block"><span className="mb-1.5 block text-sm font-semibold text-slate-700">Public URL slug</span><input required value={form.public_slug} onChange={(event) => setForm((current) => ({ ...current, public_slug: slugify(event.target.value) }))} className="input" placeholder="course-admissions" /><span className="mt-1 block text-xs text-slate-500">Customers use /chat/&lt;slug&gt; for public chat.</span></label>}
          </div>
          <label className="block"><span className="mb-1.5 block text-sm font-semibold text-slate-700">Welcome message</span><textarea required rows={3} value={form.welcome_message} onChange={(event) => setForm((current) => ({ ...current, welcome_message: event.target.value }))} className="input resize-y" /></label>
          <label className="block"><span className="mb-1.5 block text-sm font-semibold text-slate-700">Behavior instructions</span><textarea rows={4} value={form.system_instructions ?? ""} onChange={(event) => setForm((current) => ({ ...current, system_instructions: event.target.value }))} className="input resize-y" placeholder="Tone, rules, and conversation behavior specific to this receptionist..." /></label>

          <div>
            <div className="flex items-end justify-between gap-4"><div><span className="block text-sm font-semibold text-slate-700">Source knowledge</span><span className="mt-1 block text-xs text-slate-500">Select one or more existing shared knowledge items. Already-private items owned by another receptionist are unavailable.</span></div><span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700">{form.knowledge_item_ids?.length ?? 0} selected</span></div>
            <div className="mt-3 max-h-72 space-y-2 overflow-y-auto rounded-2xl border border-slate-200 bg-slate-50 p-3">
              {availableKnowledge.map((item) => {
                const checked = form.knowledge_item_ids?.includes(item.id) ?? false;
                return <button key={item.id} type="button" onClick={() => toggleKnowledge(item.id)} className={`flex w-full items-start gap-3 rounded-xl border p-3 text-left transition ${checked ? "border-indigo-300 bg-white shadow-sm" : "border-transparent bg-white/60 hover:border-slate-200 hover:bg-white"}`}><span className={`mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded border text-xs font-black ${checked ? "border-indigo-600 bg-indigo-600 text-white" : "border-slate-300 bg-white text-transparent"}`}>✓</span><span className="min-w-0"><span className="block truncate text-sm font-semibold text-slate-900">{item.title}</span><span className="mt-1 block text-xs text-slate-500">{item.category} · {item.source || "manual"} · {item.agent_id == null ? "Shared" : "Already attached to this receptionist"}</span></span></button>;
              })}
              {availableKnowledge.length === 0 && <div className="p-6 text-center text-xs leading-5 text-slate-500">No available knowledge yet. Add or upload knowledge first, then return here.</div>}
            </div>
          </div>

          <div className="flex flex-wrap justify-end gap-2"><button type="button" onClick={() => setOpen(false)} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700">Cancel</button><button type="submit" disabled={saving} className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{saving ? "Saving…" : selectedForEdit ? "Save receptionist" : "Create receptionist"}</button></div>
        </form>
      </section>}

      {loading ? <div className="rounded-2xl border border-slate-200 bg-white p-14 text-center text-sm text-slate-500">Loading your receptionists…</div> : agents.length === 0 ? <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-14 text-center"><p className="text-lg font-bold text-slate-800">No receptionists yet</p><p className="mt-2 text-sm text-slate-500">Create your first receptionist, attach the relevant knowledge, and test it before publishing.</p><button type="button" onClick={openCreate} className="mt-5 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white">Create your receptionist</button></div> : <div className="grid gap-5 lg:grid-cols-2">{agents.map((agent) => <article key={agent.id} className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-4"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-indigo-50 px-2.5 py-1 text-[11px] font-bold text-indigo-700">{agent.is_active ? "Active" : "Inactive"}</span><span className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${agent.is_published ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{agent.is_published ? "Published" : "Draft"}</span></div><h2 className="mt-3 truncate text-lg font-bold text-slate-900">{agent.name}</h2><p className="mt-1 truncate text-xs text-slate-500">/chat/{agent.public_slug}</p></div><div className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-indigo-600 font-black text-white">AI</div></div><p className="mt-4 line-clamp-2 text-sm leading-6 text-slate-600">{agent.welcome_message}</p><div className="mt-5 rounded-2xl bg-slate-50 p-4"><div className="flex items-center justify-between"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Private knowledge</p><p className="text-sm font-bold text-indigo-700">{agent.knowledge_item_ids?.length ?? 0}</p></div><div className="mt-3 flex flex-wrap gap-2">{(agent.knowledge_item_ids ?? []).slice(0, 5).map((id) => <span key={id} className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600">#{id}</span>)}{(agent.knowledge_item_ids?.length ?? 0) > 5 && <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-500">+{(agent.knowledge_item_ids?.length ?? 0) - 5} more</span>}</div></div><div className="mt-5 flex flex-wrap gap-2"><Link to={`/chat/agent/${agent.id}`} className="rounded-xl bg-indigo-600 px-3 py-2 text-xs font-bold text-white">Test receptionist</Link><a href={`/chat/${agent.public_slug}`} target="_blank" rel="noreferrer" className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-700">Open public chat</a><button type="button" onClick={() => openEdit(agent)} className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-700">Edit</button><button type="button" disabled={saving} onClick={() => void togglePublish(agent)} className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-700 disabled:opacity-50">{agent.is_published ? "Unpublish" : "Publish"}</button><button type="button" disabled={saving} onClick={() => void remove(agent)} className="rounded-xl border border-red-200 px-3 py-2 text-xs font-bold text-red-700 disabled:opacity-50">Delete</button></div></article>)}</div>}
    </div>
  );
}
