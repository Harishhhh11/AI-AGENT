import { useEffect, useMemo, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { Link } from "react-router-dom";

import { getAgents } from "../api/agents";
import type { Agent } from "../api/agents";
import { createKnowledge, deleteKnowledge, getKnowledge, updateKnowledge } from "../api/knowledge";
import type { KnowledgeCreate, KnowledgeItem } from "../api/knowledge";

const CATEGORY_PRESETS = ["Courses", "Fees", "Timings", "About Company", "Contact", "Policies", "FAQs"];
const EMPTY_FORM: KnowledgeCreate = { title: "", content: "", source: "manual", category: "Courses", agent_id: null };

export default function Knowledge() {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [search, setSearch] = useState("");
  const [scope, setScope] = useState("all");
  const [category, setCategory] = useState("all");
  const [form, setForm] = useState<KnowledgeCreate>(EMPTY_FORM);
  const [editingItem, setEditingItem] = useState<KnowledgeItem | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const [knowledgeData, agentData] = await Promise.all([getKnowledge(), getAgents()]);
        if (!mounted) return;
        setItems(knowledgeData);
        setAgents(agentData);
      } catch (reason) {
        if (mounted) setError(reason instanceof Error ? reason.message : "Unable to load knowledge.");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    void load();
    return () => { mounted = false; };
  }, []);

  const categories = useMemo(() => Array.from(new Set([...CATEGORY_PRESETS, ...items.map((item) => item.category).filter(Boolean)])), [items]);
  const visibleItems = useMemo(() => {
    const query = search.trim().toLowerCase();
    return items.filter((item) => {
      if (scope === "shared" && item.agent_id !== null) return false;
      if (scope.startsWith("agent:") && item.agent_id !== Number(scope.slice(6))) return false;
      if (category !== "all" && item.category !== category) return false;
      if (!query) return true;
      return [item.title, item.content, item.source, item.category].some((value) => value.toLowerCase().includes(query));
    });
  }, [items, search, scope, category]);

  function closeForm() { setFormOpen(false); setEditingItem(null); setForm({ ...EMPTY_FORM }); }
  function openNewItem() {
    const selectedAgent = scope.startsWith("agent:") ? Number(scope.slice(6)) : null;
    setForm({ ...EMPTY_FORM, category: category === "all" ? "Courses" : category, agent_id: selectedAgent });
    setEditingItem(null); setError(""); setSuccess(""); setFormOpen(true);
  }
  function openEditItem(item: KnowledgeItem) {
    setEditingItem(item); setForm({ title: item.title, content: item.content, source: item.source, category: item.category, agent_id: item.agent_id });
    setError(""); setSuccess(""); setFormOpen(true);
  }
  function replaceItem(updated: KnowledgeItem) { setItems((current) => current.map((item) => item.id === updated.id ? updated : item)); }

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const title = form.title.trim(); const content = form.content.trim(); const source = form.source.trim() || "manual"; const selectedCategory = form.category.trim();
    if (!title || !content || !selectedCategory) { setError("Add a title, category, and the information your receptionist should use."); return; }
    setSaving(true); setError(""); setSuccess("");
    try {
      if (editingItem) {
        replaceItem(await updateKnowledge(editingItem.id, { title, content, source, category: selectedCategory, agent_id: form.agent_id ?? null }));
        setSuccess("Knowledge updated and assigned to the selected scope.");
      } else {
        const created = await createKnowledge({ title, content, source, category: selectedCategory, agent_id: form.agent_id ?? null });
        setItems((current) => [created, ...current]); setSuccess("Knowledge added, indexed, and assigned to the selected scope.");
      }
      closeForm();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to save knowledge."); }
    finally { setSaving(false); }
  }

  async function toggleActive(item: KnowledgeItem) {
    if (saving) return; setSaving(true); setError(""); setSuccess("");
    try { replaceItem(await updateKnowledge(item.id, { is_active: !item.is_active })); setSuccess(item.is_active ? "Knowledge item deactivated." : "Knowledge item activated."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to update this knowledge item."); }
    finally { setSaving(false); }
  }

  async function removeItem(item: KnowledgeItem) {
    if (saving || !window.confirm(`Delete "${item.title}"? This cannot be undone.`)) return;
    setSaving(true); setError(""); setSuccess("");
    try { await deleteKnowledge(item.id); setItems((current) => current.filter((value) => value.id !== item.id)); setSuccess("Knowledge item deleted."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to delete this knowledge item."); }
    finally { setSaving(false); }
  }

  const scopeName = (agentId: number | null) => agentId == null ? "Shared with all receptionists" : agents.find((agent) => agent.id === agentId)?.name ?? `Receptionist #${agentId}`;

  return <div className="space-y-6">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">AI foundation</p><h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Knowledge Management</h1><p className="mt-1 text-sm text-slate-500">Control exactly which verified facts each receptionist can use.</p></div>
      <div className="flex flex-wrap gap-2"><button type="button" onClick={() => window.location.reload()} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700">Refresh</button><Link to="/documents" className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700">Upload documents</Link><button type="button" onClick={openNewItem} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white">+ Add knowledge</button></div>
    </div>

    <div className="grid gap-3 sm:grid-cols-3"><Metric label="Knowledge items" value={items.length} /><Metric label="Active" value={items.filter((item) => item.is_active).length} tone="text-emerald-600" /><Metric label="Receptionists" value={agents.length} tone="text-indigo-600" /></div>
    {error && <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</div>}
    {success && <div role="status" className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">{success}</div>}

    {formOpen && <section className="rounded-2xl border border-indigo-100 bg-white p-5 shadow-lg sm:p-6"><div className="flex items-start justify-between gap-4"><div><h2 className="font-bold text-slate-900">{editingItem ? "Edit knowledge" : "Add knowledge"}</h2><p className="mt-1 text-sm text-slate-500">The selected scope is persisted and enforced during retrieval.</p></div><button type="button" onClick={closeForm} className="rounded-lg px-2 py-1 text-sm text-slate-500">Close</button></div><form onSubmit={submitForm} className="mt-6 space-y-5"><div className="grid gap-4 sm:grid-cols-2"><Field label="Title"><input required value={form.title} onChange={(e) => setForm((v) => ({ ...v, title: e.target.value }))} className="input" /></Field><Field label="Source"><input value={form.source} onChange={(e) => setForm((v) => ({ ...v, source: e.target.value }))} className="input" /></Field></div><Field label="Category"><input required list="knowledge-categories" value={form.category} onChange={(e) => setForm((v) => ({ ...v, category: e.target.value }))} className="input" /><datalist id="knowledge-categories">{categories.map((item) => <option key={item} value={item} />)}</datalist></Field><Field label="Receptionist scope"><select value={form.agent_id ?? ""} onChange={(e) => setForm((v) => ({ ...v, agent_id: e.target.value ? Number(e.target.value) : null }))} className="input"><option value="">Shared with all receptionists</option>{agents.map((agent) => <option key={agent.id} value={agent.id}>{agent.name} only</option>)}</select></Field><Field label="Information"><textarea required value={form.content} onChange={(e) => setForm((v) => ({ ...v, content: e.target.value }))} rows={8} className="input resize-y leading-6" placeholder="Write verified information the AI should use..." /></Field><div className="flex justify-end gap-2"><button type="button" onClick={closeForm} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700">Cancel</button><button type="submit" disabled={saving} className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{saving ? "Saving…" : editingItem ? "Save changes" : "Add knowledge"}</button></div></form></section>}

    <div className="rounded-2xl border border-slate-200/80 bg-white p-3 shadow-sm"><div className="grid gap-3 md:grid-cols-[1fr_auto] md:items-center"><input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search titles, information, sources..." className="input" /><select value={scope} onChange={(e) => setScope(e.target.value)} className="input md:min-w-64"><option value="all">All scopes</option><option value="shared">Shared</option>{agents.map((agent) => <option key={agent.id} value={`agent:${agent.id}`}>{agent.name} only</option>)}</select></div><div className="mt-3 flex gap-2 overflow-x-auto pb-1">{["all", ...categories].map((item) => <button key={item} type="button" onClick={() => setCategory(item)} className={`shrink-0 rounded-full px-3 py-2 text-xs font-semibold ${category === item ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600"}`}>{item === "all" ? "All categories" : item}</button>)}</div></div>

    {loading ? <div className="rounded-2xl border border-slate-200 bg-white p-14 text-center text-sm text-slate-500">Loading knowledge base…</div> : visibleItems.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-14 text-center"><p className="text-lg font-bold text-slate-800">No knowledge found</p><p className="mt-2 text-sm text-slate-500">Add verified company information or upload a source document.</p><button type="button" onClick={openNewItem} className="mt-5 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white">Add knowledge</button></div> : <div className="grid gap-4 lg:grid-cols-2">{visibleItems.map((item) => <article key={item.id} className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm"><div><div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-indigo-50 px-2.5 py-1 text-[11px] font-semibold text-indigo-700">{item.category}</span><span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${item.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{item.is_active ? "Active" : "Inactive"}</span></div><h2 className="mt-3 truncate font-bold text-slate-900">{item.title}</h2><p className="mt-1 text-xs text-slate-500">{scopeName(item.agent_id)} · Source: {item.source || "manual"}</p></div><p className="mt-4 line-clamp-4 whitespace-pre-wrap text-sm leading-6 text-slate-600">{item.content}</p><div className="mt-5 flex flex-wrap gap-2 border-t border-slate-100 pt-4"><button type="button" onClick={() => openEditItem(item)} className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700">Edit</button><button type="button" disabled={saving} onClick={() => void toggleActive(item)} className={`rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50 ${item.is_active ? "border border-amber-200 text-amber-700" : "bg-emerald-600 text-white"}`}>{item.is_active ? "Deactivate" : "Activate"}</button><button type="button" disabled={saving} onClick={() => void removeItem(item)} className="rounded-xl border border-red-200 px-3 py-2 text-xs font-semibold text-red-700 disabled:opacity-50">Delete</button></div></article>)}</div>}
  </div>;
}

function Field({ label, children }: { label: string; children: ReactNode }) { return <label className="block"><span className="mb-1.5 block text-sm font-semibold text-slate-700">{label}</span>{children}</label>; }
function Metric({ label, value, tone = "text-slate-900" }: { label: string; value: number; tone?: string }) { return <div className="rounded-2xl border border-slate-200/80 bg-white px-4 py-3 shadow-sm"><p className="text-xs font-medium text-slate-500">{label}</p><p className={`mt-1 text-2xl font-bold ${tone}`}>{value}</p></div>; }
