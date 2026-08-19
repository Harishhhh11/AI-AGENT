import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { deleteLead, getLeads, updateLead } from "../api/leads";
import type { Lead } from "../api/leads";

const STATUSES = ["all", "new", "contacted", "qualified", "converted", "lost"];
const EDIT_FIELDS = [
  ["name", "Name"],
  ["phone", "Phone"],
  ["email", "Email"],
  ["interest", "Interest"],
  ["preferred_mode", "Preferred mode"],
  ["preferred_time", "Preferred time"],
] as const;

type EditField = (typeof EDIT_FIELDS)[number][0];
type LeadForm = Record<EditField | "notes", string>;

function emptyForm(lead?: Lead): LeadForm {
  return {
    name: lead?.name ?? "",
    phone: lead?.phone ?? "",
    email: lead?.email ?? "",
    interest: lead?.interest ?? "",
    preferred_mode: lead?.preferred_mode ?? "",
    preferred_time: lead?.preferred_time ?? "",
    notes: lead?.notes ?? "",
  };
}

function labelForStatus(status: string) {
  return status ? `${status.charAt(0).toUpperCase()}${status.slice(1)}` : "Unknown";
}

function statusClass(status: string) {
  const styles: Record<string, string> = {
    new: "bg-blue-50 text-blue-700 ring-blue-100",
    contacted: "bg-amber-50 text-amber-700 ring-amber-100",
    qualified: "bg-violet-50 text-violet-700 ring-violet-100",
    converted: "bg-emerald-50 text-emerald-700 ring-emerald-100",
    lost: "bg-red-50 text-red-700 ring-red-100",
  };
  return styles[status] ?? "bg-slate-100 text-slate-600 ring-slate-200";
}

export default function Leads() {
  const navigate = useNavigate();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshToken, setRefreshToken] = useState(0);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<LeadForm>(emptyForm());

  useEffect(() => {
    let cancelled = false;

    async function loadLeads() {
      setLoading(true);
      setError("");
      try {
        const data = await getLeads();
        if (!cancelled) setLeads(data);
      } catch (err) {
        console.error("Failed to load leads:", err);
        if (!cancelled) setError("Unable to load leads. Please try again.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadLeads();
    return () => { cancelled = true; };
  }, [refreshToken]);

  const counts = useMemo(() => leads.reduce<Record<string, number>>((result, lead) => {
    result[lead.status] = (result[lead.status] ?? 0) + 1;
    return result;
  }, {}), [leads]);

  const filteredLeads = useMemo(() => {
    const query = search.trim().toLowerCase();
    return leads.filter((lead) => {
      if (status !== "all" && lead.status !== status) return false;
      if (!query) return true;
      return [lead.name, lead.phone, lead.email, lead.interest, lead.preferred_mode, lead.preferred_time, lead.notes]
        .some((value) => value?.toLowerCase().includes(query));
    });
  }, [leads, search, status]);

  const hasFilters = Boolean(search.trim()) || status !== "all";

  function selectLead(lead: Lead) {
    setSelectedLead(lead);
    setEditing(false);
    setForm(emptyForm(lead));
  }

  function replaceLead(updatedLead: Lead) {
    setLeads((current) => current.map((lead) => lead.id === updatedLead.id ? updatedLead : lead));
    setSelectedLead(updatedLead);
  }

  async function changeStatus(newStatus: string) {
    if (!selectedLead || newStatus === selectedLead.status || saving) return;
    setSaving(true);
    setError("");
    try {
      replaceLead(await updateLead(selectedLead.id, { status: newStatus }));
    } catch (err) {
      console.error("Failed to update status:", err);
      setError("Unable to update lead status.");
    } finally {
      setSaving(false);
    }
  }

  async function saveLead() {
    if (!selectedLead || saving) return;
    setSaving(true);
    setError("");
    try {
      const updatedLead = await updateLead(selectedLead.id, {
        name: form.name.trim() || null,
        phone: form.phone.trim() || null,
        email: form.email.trim() || null,
        interest: form.interest.trim() || null,
        preferred_mode: form.preferred_mode.trim() || null,
        preferred_time: form.preferred_time.trim() || null,
        notes: form.notes.trim() || null,
      });
      replaceLead(updatedLead);
      setEditing(false);
    } catch (err) {
      console.error("Failed to save lead:", err);
      setError("Unable to save lead changes.");
    } finally {
      setSaving(false);
    }
  }

  async function removeLead() {
    if (!selectedLead || saving) return;
    const description = selectedLead.name || selectedLead.email || "this lead";
    if (!window.confirm(`Delete ${description}? This cannot be undone.`)) return;

    setSaving(true);
    setError("");
    try {
      await deleteLead(selectedLead.id);
      setLeads((current) => current.filter((lead) => lead.id !== selectedLead.id));
      setSelectedLead(null);
      setEditing(false);
    } catch (err) {
      console.error("Failed to delete lead:", err);
      setError("Unable to delete lead.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Customer pipeline</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Leads</h1>
          <p className="mt-1 text-sm text-slate-500">Manage every customer captured by your AI receptionist.</p>
        </div>
        <button type="button" onClick={() => setRefreshToken((value) => value + 1)} disabled={loading} className="inline-flex w-fit items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-indigo-200 hover:text-indigo-700 disabled:cursor-not-allowed disabled:opacity-50">
          Refresh leads
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        {[
          ["All leads", leads.length, "bg-slate-950 text-white", "all"],
          ["New", counts.new ?? 0, "bg-blue-50 text-blue-800", "new"],
          ["Contacted", counts.contacted ?? 0, "bg-amber-50 text-amber-800", "contacted"],
          ["Qualified", counts.qualified ?? 0, "bg-violet-50 text-violet-800", "qualified"],
          ["Converted", counts.converted ?? 0, "bg-emerald-50 text-emerald-800", "converted"],
        ].map(([label, value, tone, filter]) => (
          <button key={String(label)} type="button" onClick={() => setStatus(String(filter))} className={`rounded-2xl border border-slate-200/80 p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${tone} ${status === filter ? "ring-2 ring-indigo-400 ring-offset-2" : ""}`}>
            <p className="text-xs font-medium opacity-75">{label}</p>
            <p className="mt-2 text-2xl font-bold">{loading ? "-" : value}</p>
          </button>
        ))}
      </div>

      {error && <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</div>}

      <div className="grid gap-3 rounded-2xl border border-slate-200/80 bg-white p-3 shadow-sm md:grid-cols-[1fr_13rem_auto]">
        <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by name, phone, email, course, or note..." className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none transition focus:border-indigo-500 focus:bg-white focus:ring-4 focus:ring-indigo-500/10" />
        <select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10">
          {STATUSES.map((item) => <option key={item} value={item}>{item === "all" ? "All statuses" : labelForStatus(item)}</option>)}
        </select>
        {hasFilters && <button type="button" onClick={() => { setSearch(""); setStatus("all"); }} className="rounded-xl px-3 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-slate-100 hover:text-slate-900">Clear filters</button>}
      </div>

      <div className="flex items-center justify-between text-sm text-slate-500">
        <p>Showing <span className="font-semibold text-slate-900">{filteredLeads.length}</span> of {leads.length} leads</p>
        {loading && <span>Loading...</span>}
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_12px_40px_rgba(15,23,42,0.06)]">
        {loading ? (
          <div className="p-14 text-center"><div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-indigo-600" /><p className="mt-4 text-sm text-slate-500">Loading leads...</p></div>
        ) : filteredLeads.length === 0 ? (
          <div className="p-14 text-center"><div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-lg font-bold text-indigo-600">L</div><p className="mt-4 font-semibold text-slate-800">No leads found</p><p className="mt-1 text-sm text-slate-500">New leads from customer conversations appear here.</p></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[850px] text-left">
              <thead className="border-b border-slate-200 bg-slate-50/80"><tr>
                <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-slate-500">Customer</th>
                <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-slate-500">Phone</th>
                <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-slate-500">Interest</th>
                <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-slate-500">Mode</th>
                <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-slate-500">Status</th>
                <th className="px-5 py-4 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">Actions</th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {filteredLeads.map((lead) => <tr key={lead.id} className="transition hover:bg-indigo-50/30">
                  <td className="px-5 py-4"><button type="button" onClick={() => selectLead(lead)} className="text-left"><p className="font-semibold text-slate-900">{lead.name || "Unknown customer"}</p><p className="mt-1 max-w-[15rem] truncate text-xs text-slate-500">{lead.email || "No email provided"}</p></button></td>
                  <td className="px-5 py-4 text-sm text-slate-600">{lead.phone || "-"}</td>
                  <td className="px-5 py-4 text-sm text-slate-600">{lead.interest || "-"}</td>
                  <td className="px-5 py-4 text-sm text-slate-600">{lead.preferred_mode || "-"}</td>
                  <td className="px-5 py-4"><span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${statusClass(lead.status)}`}>{labelForStatus(lead.status)}</span></td>
                  <td className="px-5 py-4 text-right"><button type="button" onClick={() => selectLead(lead)} className="rounded-lg px-3 py-2 text-sm font-semibold text-indigo-700 transition hover:bg-indigo-50">View</button></td>
                </tr>)}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedLead && <div className="fixed inset-0 z-50 flex justify-end">
        <button type="button" aria-label="Close lead details" onClick={() => { setSelectedLead(null); setEditing(false); }} className="absolute inset-0 bg-slate-950/40 backdrop-blur-sm" />
        <aside className="relative h-full w-full max-w-xl overflow-y-auto bg-white shadow-2xl">
          <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white/95 px-5 py-4 backdrop-blur sm:px-6">
            <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">Lead record</p><h2 className="mt-1 text-lg font-bold text-slate-900">{selectedLead.name || "Unknown customer"}</h2></div>
            <button type="button" onClick={() => { setSelectedLead(null); setEditing(false); }} className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50">Close</button>
          </div>

          <div className="space-y-6 p-5 sm:p-6">
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-slate-50 p-4">
              <div><p className="text-xs text-slate-500">Lead status</p><p className="mt-1 text-sm font-semibold text-slate-900">{labelForStatus(selectedLead.status)}</p></div>
              <select value={selectedLead.status} disabled={saving} onChange={(event) => void changeStatus(event.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 outline-none focus:border-indigo-500 disabled:opacity-50">
                {STATUSES.slice(1).map((item) => <option key={item} value={item}>{labelForStatus(item)}</option>)}
              </select>
            </div>

            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={() => { setForm(emptyForm(selectedLead)); setEditing(true); }} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700">Edit lead</button>
              {selectedLead.conversation_id && <button type="button" onClick={() => navigate(`/conversations/${selectedLead.conversation_id}`)} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">View conversation</button>}
              <button type="button" onClick={() => void removeLead()} disabled={saving} className="rounded-xl border border-red-200 px-4 py-2.5 text-sm font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50">Delete</button>
            </div>

            {editing ? <div className="space-y-4 rounded-2xl border border-indigo-100 bg-indigo-50/40 p-4 sm:p-5">
              <div><h3 className="font-semibold text-slate-900">Edit lead details</h3><p className="mt-1 text-xs text-slate-500">Update what the customer shared with your assistant.</p></div>
              <div className="grid gap-4 sm:grid-cols-2">{EDIT_FIELDS.map(([field, label]) => <label key={field} className="block"><span className="text-xs font-semibold text-slate-600">{label}</span><input value={form[field]} onChange={(event) => setForm((current) => ({ ...current, [field]: event.target.value }))} className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10" /></label>)}</div>
              <label className="block"><span className="text-xs font-semibold text-slate-600">Notes</span><textarea value={form.notes} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} rows={4} className="mt-1.5 w-full resize-y rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10" /></label>
              <div className="flex gap-2"><button type="button" onClick={() => void saveLead()} disabled={saving} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">{saving ? "Saving..." : "Save changes"}</button><button type="button" onClick={() => setEditing(false)} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-white">Cancel</button></div>
            </div> : <LeadDetails lead={selectedLead} />}
          </div>
        </aside>
      </div>}
    </div>
  );
}

function LeadDetails({ lead }: { lead: Lead }) {
  const details = [
    ["Phone", lead.phone], ["Email", lead.email], ["Interest", lead.interest],
    ["Preferred mode", lead.preferred_mode], ["Preferred time", lead.preferred_time],
  ];

  return <div className="space-y-5">
    <div className="grid gap-4 sm:grid-cols-2">{details.map(([label, value]) => <div key={label} className="rounded-2xl border border-slate-200 p-4"><p className="text-xs font-medium text-slate-500">{label}</p><p className="mt-2 break-words text-sm font-semibold text-slate-800">{value || "Not provided"}</p></div>)}</div>
    <div className="rounded-2xl border border-slate-200 p-4"><p className="text-xs font-medium text-slate-500">Notes</p><p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{lead.notes || "No notes available."}</p></div>
  </div>;
}
