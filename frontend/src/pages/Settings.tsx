import { useEffect, useState } from "react";
import { getOrganization, updateOrganization, type Organization } from "../api/admin";

export default function Settings() {
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [form, setForm] = useState({ name: "", email: "" });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getOrganization()
      .then((data) => { setOrganization(data); setForm({ name: data.name, email: data.email }); })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unable to load settings."));
  }, []);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organization) return;
    setSaving(true);
    setSaved(false);
    setError("");
    try {
      const updated = await updateOrganization(organization.id, form);
      setOrganization(updated);
      setForm({ name: updated.name, email: updated.email });
      setSaved(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save settings.");
    } finally {
      setSaving(false);
    }
  }

  return <div className="max-w-3xl space-y-6">
    <header><p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Workspace configuration</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Settings</h1><p className="mt-1 text-sm text-slate-500">Keep your company profile and workspace identity up to date.</p></header>
    {error && <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
    {saved && <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">Settings saved successfully.</div>}
    <form onSubmit={submit} className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
      <div><label className="mb-1.5 block text-sm font-semibold text-slate-700" htmlFor="company-name">Company name</label><input id="company-name" required minLength={2} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" /></div>
      <div><label className="mb-1.5 block text-sm font-semibold text-slate-700" htmlFor="company-email">Company email</label><input id="company-email" required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input" /></div>
      <div className="flex justify-end"><button disabled={saving || !organization} className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{saving ? "Saving…" : "Save changes"}</button></div>
    </form>
  </div>;
}
