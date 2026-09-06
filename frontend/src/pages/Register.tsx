import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerCompany } from "../api/auth";

const initialForm = {
  organization_name: "", organization_email: "", first_name: "", last_name: "",
  admin_email: "", password: "", phone: "", agent_name: "AI Receptionist", public_slug: "",
};

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const update = (name: keyof typeof initialForm, value: string) => setForm((current) => ({ ...current, [name]: value }));

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(""); setLoading(true);
    try {
      await registerCompany(form);
      navigate("/login", { replace: true, state: { message: "Workspace created. Sign in to continue." } });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create workspace.");
    } finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-8 text-slate-900 sm:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-6xl overflow-hidden rounded-[2rem] bg-white shadow-2xl lg:grid-cols-[0.85fr_1.15fr]">
        <aside className="hidden bg-gradient-to-br from-indigo-600 via-violet-600 to-slate-950 p-10 text-white lg:flex lg:flex-col lg:justify-between">
          <div><div className="flex items-center gap-3 text-sm font-bold"><span className="grid h-10 w-10 place-items-center rounded-2xl bg-white/15">AI</span> AI Receptionist</div><h1 className="mt-24 text-4xl font-bold leading-tight">Launch a calmer way to handle every enquiry.</h1><p className="mt-5 max-w-sm text-sm leading-7 text-indigo-100">Create your workspace, train your receptionist, and turn conversations into qualified opportunities.</p></div>
          <div className="grid grid-cols-3 gap-3 text-center text-xs text-indigo-100"><span className="rounded-2xl bg-white/10 p-3">24/7<br /><b className="text-white">Coverage</b></span><span className="rounded-2xl bg-white/10 p-3">One<br /><b className="text-white">Workspace</b></span><span className="rounded-2xl bg-white/10 p-3">Clear<br /><b className="text-white">Insights</b></span></div>
        </aside>
        <main className="p-6 sm:p-10 lg:p-14">
          <div className="mb-8 flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-indigo-600">Get started</p><h2 className="mt-2 text-3xl font-bold tracking-tight">Create your workspace</h2><p className="mt-2 text-sm text-slate-500">Everything you need to launch your AI receptionist.</p></div><Link to="/login" className="text-sm font-semibold text-indigo-600 hover:text-indigo-800">Sign in</Link></div>
          <form onSubmit={submit} className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Company name" value={form.organization_name} onChange={(v) => update("organization_name", v)} required />
              <Field label="Company email" type="email" value={form.organization_email} onChange={(v) => update("organization_email", v)} required />
              <Field label="Your first name" value={form.first_name} onChange={(v) => update("first_name", v)} required />
              <Field label="Your last name" value={form.last_name} onChange={(v) => update("last_name", v)} required />
              <Field label="Admin email" type="email" value={form.admin_email} onChange={(v) => update("admin_email", v)} required />
              <Field label="Phone (optional)" value={form.phone} onChange={(v) => update("phone", v)} />
              <Field label="Receptionist name" value={form.agent_name} onChange={(v) => update("agent_name", v)} required />
              <Field label="Public URL slug" value={form.public_slug} onChange={(v) => update("public_slug", v.toLowerCase().replace(/\s+/g, "-"))} placeholder="your-company" required />
              <Field label="Password" type="password" value={form.password} onChange={(v) => update("password", v)} minLength={8} required />
            </div>
            {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
            <button disabled={loading} className="w-full rounded-xl bg-indigo-600 px-4 py-3.5 text-sm font-bold text-white shadow-lg shadow-indigo-600/20 transition hover:bg-indigo-700 disabled:opacity-60">{loading ? "Creating workspace…" : "Create workspace"}</button>
          </form>
        </main>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, type = "text", ...props }: { label: string; value: string; onChange: (value: string) => void; type?: string; [key: string]: unknown }) {
  return <label className="block text-sm font-semibold text-slate-700">{label}<input {...props} type={type} value={value} onChange={(event) => onChange(event.target.value)} className="input mt-2" /></label>;
}
