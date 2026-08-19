import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { createKnowledge, deleteKnowledge, getKnowledge, updateKnowledge } from "../api/knowledge";
import type { KnowledgeCreate, KnowledgeItem } from "../api/knowledge";
import { getAgents } from "../api/agents";
import type { Agent } from "../api/agents";

const CATEGORY_PRESETS = [
  "Courses", "Fees", "Timings", "About Company", "Contact", "Policies", "FAQs",
];

const EMPTY_FORM: KnowledgeCreate = { title: "", content: "", source: "manual", category: "Courses" };

export default function Knowledge() {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [form, setForm] = useState<KnowledgeCreate>(EMPTY_FORM);
  const [editingItem, setEditingItem] = useState<KnowledgeItem | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [refreshToken, setRefreshToken] = useState(0);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function loadKnowledge() {
      setLoading(true);
      setError("");
      try {
        const data = await getKnowledge();
        if (!cancelled) setItems(data);
      } catch (err) {
        console.error("Knowledge loading error:", err);
        if (!cancelled) setError(err instanceof Error ? err.message : "Unable to load knowledge.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadKnowledge();
    return () => { cancelled = true; };
  }, [refreshToken]);

  useEffect(() => {
    void getAgents().then(setAgents).catch(() => {
      // Knowledge remains usable when no receptionist has been created.
    });
  }, []);

  const availableCategories = useMemo(() => Array.from(new Set([
    ...CATEGORY_PRESETS,
    ...items.map((item) => item.category).filter(Boolean),
  ])), [items]);

  const visibleItems = useMemo(() => {
    const query = search.trim().toLowerCase();
    return items.filter((item) => {
      if (category !== "all" && item.category !== category) return false;
      if (!query) return true;
      return [item.title, item.content, item.source, item.category]
        .some((value) => value.toLowerCase().includes(query));
    });
  }, [items, search, category]);

  const activeCount = items.filter((item) => item.is_active).length;

  function closeForm() {
    setFormOpen(false);
    setEditingItem(null);
    setForm(EMPTY_FORM);
  }

  function openNewItem() {
    setForm({ ...EMPTY_FORM, category: category === "all" ? "Courses" : category });
    setEditingItem(null);
    setError("");
    setSuccess("");
    setFormOpen(true);
  }

  function openEditItem(item: KnowledgeItem) {
    setEditingItem(item);
    setForm({ title: item.title, content: item.content, source: item.source, category: item.category, agent_id: item.agent_id });
    setError("");
    setSuccess("");
    setFormOpen(true);
  }

  function replaceItem(updated: KnowledgeItem) {
    setItems((current) => current.map((item) => item.id === updated.id ? updated : item));
  }

  async function submitForm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const title = form.title.trim();
    const content = form.content.trim();
    const source = form.source.trim() || "manual";
    const selectedCategory = form.category.trim();
    if (!title || !content || !selectedCategory) {
      setError("Add a title, category, and the information your receptionist should use.");
      return;
    }

    setSaving(true);
    setError("");
    setSuccess("");
    try {
      if (editingItem) {
        replaceItem(await updateKnowledge(editingItem.id, { title, content, source, category: selectedCategory }));
        setSuccess("Knowledge updated and re-indexed for the AI receptionist.");
      } else {
        const created = await createKnowledge({ title, content, source, category: selectedCategory, agent_id: form.agent_id ?? null });
        setItems((current) => [created, ...current]);
        setSuccess("Knowledge added and indexed for the AI receptionist.");
      }
      closeForm();
    } catch (err) {
      console.error("Knowledge save error:", err);
      setError(err instanceof Error ? err.message : "Unable to save knowledge.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(item: KnowledgeItem) {
    if (saving) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      replaceItem(await updateKnowledge(item.id, { is_active: !item.is_active }));
      setSuccess(item.is_active ? "Knowledge item deactivated." : "Knowledge item activated for the AI receptionist.");
    } catch (err) {
      console.error("Knowledge activation error:", err);
      setError("Unable to update this knowledge item.");
    } finally {
      setSaving(false);
    }
  }

  async function removeItem(item: KnowledgeItem) {
    if (saving || !window.confirm(`Delete "${item.title}"? This cannot be undone.`)) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      await deleteKnowledge(item.id);
      setItems((current) => current.filter((currentItem) => currentItem.id !== item.id));
      setSuccess("Knowledge item deleted.");
    } catch (err) {
      console.error("Knowledge delete error:", err);
      setError("Unable to delete this knowledge item.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">AI foundation</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Knowledge Management</h1>
          <p className="mt-1 text-sm text-slate-500">Control the facts, policies, and answers your AI receptionist can use.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => setRefreshToken((value) => value + 1)} disabled={loading} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm hover:border-indigo-200 hover:text-indigo-700 disabled:opacity-50">Refresh</button>
          <Link to="/documents" className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm hover:border-indigo-200 hover:text-indigo-700">Upload documents</Link>
          <button type="button" onClick={openNewItem} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-700">+ Add knowledge</button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <Metric label="Knowledge items" value={items.length} tone="text-slate-900" />
        <Metric label="Active for AI" value={activeCount} tone="text-emerald-600" />
        <Metric label="Categories" value={availableCategories.length} tone="text-indigo-600" />
      </div>

      {error && <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</div>}
      {success && <div role="status" className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">{success}</div>}

      {formOpen && <div className="rounded-2xl border border-indigo-100 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,0.07)] sm:p-6">
        <div className="flex items-start justify-between gap-4"><div><h2 className="font-bold text-slate-900">{editingItem ? "Edit knowledge" : "Add knowledge"}</h2><p className="mt-1 text-sm text-slate-500">Saving changes automatically updates the semantic index.</p></div><button type="button" onClick={closeForm} className="rounded-lg px-2 py-1 text-sm font-semibold text-slate-500 hover:bg-slate-100">Close</button></div>
        <form onSubmit={submitForm} className="mt-6 space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Title"><input required value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} placeholder="e.g. Python course fee" className="input" /></Field>
            <Field label="Source"><input value={form.source} onChange={(event) => setForm((current) => ({ ...current, source: event.target.value }))} placeholder="Website, brochure, or manual" className="input" /></Field>
          </div>
          <Field label="Category"><input required list="knowledge-categories" value={form.category} onChange={(event) => setForm((current) => ({ ...current, category: event.target.value }))} placeholder="Choose or type a category" className="input" /><datalist id="knowledge-categories">{availableCategories.map((item) => <option key={item} value={item} />)}</datalist></Field>
          {!editingItem && agents.length > 0 && <Field label="Receptionist scope"><select value={form.agent_id ?? ""} onChange={(event) => setForm((current) => ({ ...current, agent_id: event.target.value ? Number(event.target.value) : null }))} className="input"><option value="">Shared with all receptionists</option>{agents.map((agent) => <option key={agent.id} value={agent.id}>{agent.name} only</option>)}</select><p className="mt-1 text-xs text-slate-500">Shared knowledge is available to every receptionist in this company.</p></Field>}
          <Field label="Information"><textarea required value={form.content} onChange={(event) => setForm((current) => ({ ...current, content: event.target.value }))} rows={8} placeholder="Write the verified information the AI should use when answering customers..." className="input resize-y leading-6" /></Field>
          <div className="flex flex-wrap justify-end gap-2"><button type="button" onClick={closeForm} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">Cancel</button><button type="submit" disabled={saving} className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50">{saving ? "Saving..." : editingItem ? "Save changes" : "Add knowledge"}</button></div>
        </form>
      </div>}

      <div className="rounded-2xl border border-slate-200/80 bg-white p-3 shadow-sm">
        <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search titles, information, sources, and categories..." className="input" />
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {["all", ...availableCategories].map((item) => <button key={item} type="button" onClick={() => setCategory(item)} className={`shrink-0 rounded-full px-3 py-2 text-xs font-semibold transition ${category === item ? "bg-indigo-600 text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-indigo-50 hover:text-indigo-700"}`}>{item === "all" ? "All knowledge" : item}</button>)}
        </div>
      </div>

      <div className="flex items-center justify-between text-sm text-slate-500"><p>Showing <span className="font-semibold text-slate-900">{visibleItems.length}</span> of {items.length} items</p>{loading && <span>Loading...</span>}</div>

      {loading ? <div className="rounded-2xl border border-slate-200 bg-white p-14 text-center shadow-sm"><div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-indigo-600" /><p className="mt-4 text-sm text-slate-500">Loading knowledge base...</p></div>
        : visibleItems.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-14 text-center"><p className="text-lg font-bold text-slate-800">No knowledge found</p><p className="mt-2 text-sm text-slate-500">Add verified company information or upload a source document.</p><button type="button" onClick={openNewItem} className="mt-5 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white">Add knowledge</button></div>
        : <div className="grid gap-4 lg:grid-cols-2">{visibleItems.map((item) => <article key={item.id} className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_8px_30px_rgba(15,23,42,0.04)] transition hover:border-indigo-200">
          <div className="flex items-start justify-between gap-3"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-indigo-50 px-2.5 py-1 text-[11px] font-semibold text-indigo-700">{item.category}</span><span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${item.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{item.is_active ? "Active" : "Inactive"}</span></div><h2 className="mt-3 truncate font-bold text-slate-900">{item.title}</h2><p className="mt-1 text-xs text-slate-500">Source: {item.source || "manual"}</p></div></div>
          <p className="mt-4 line-clamp-4 whitespace-pre-wrap text-sm leading-6 text-slate-600">{item.content}</p>
          <div className="mt-5 flex flex-wrap gap-2 border-t border-slate-100 pt-4"><button type="button" onClick={() => openEditItem(item)} className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50">Edit</button><button type="button" disabled={saving} onClick={() => void toggleActive(item)} className={`rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50 ${item.is_active ? "border border-amber-200 text-amber-700 hover:bg-amber-50" : "bg-emerald-600 text-white hover:bg-emerald-700"}`}>{item.is_active ? "Deactivate" : "Activate"}</button><button type="button" disabled={saving} onClick={() => void removeItem(item)} className="rounded-xl border border-red-200 px-3 py-2 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50">Delete</button></div>
        </article>)}</div>}
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: number; tone: string }) {
  return <div className="rounded-2xl border border-slate-200/80 bg-white px-4 py-3 shadow-sm"><p className="text-xs font-medium text-slate-500">{label}</p><p className={`mt-1 text-2xl font-bold ${tone}`}>{value}</p></div>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block"><span className="mb-1.5 block text-sm font-semibold text-slate-700">{label}</span>{children}</label>;
}
