import { useEffect, useState } from "react";
import {
  createTeamMember,
  deleteTeamMember,
  getOrganization,
  getRoles,
  getTeamMembers,
  type Organization,
  type Role,
  type TeamMember,
} from "../api/admin";

const emptyForm = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  password: "",
};

export default function Team() {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getTeamMembers(), getRoles(), getOrganization()])
      .then(([memberData, roleData, organizationData]) => {
        setMembers(memberData);
        setRoles(roleData);
        setOrganization(organizationData);
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unable to load team."));
  }, []);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organization) return;
    setSaving(true);
    setError("");
    try {
      const member = await createTeamMember({ ...form, organization_id: organization.id });
      setMembers((current) => [...current, member]);
      setForm(emptyForm);
      setOpen(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to add team member.");
    } finally {
      setSaving(false);
    }
  }

  async function remove(member: TeamMember) {
    if (!window.confirm(`Remove ${member.first_name} ${member.last_name} from the workspace?`)) return;
    setError("");
    try {
      await deleteTeamMember(member.id);
      setMembers((current) => current.filter((item) => item.id !== member.id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to remove team member.");
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Workspace access</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Team management</h1>
          <p className="mt-1 text-sm text-slate-500">Manage who can operate your AI receptionist workspace.</p>
        </div>
        <button onClick={() => setOpen(true)} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-700">+ Add member</button>
      </header>
      {error && <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
      {open && <form onSubmit={submit} className="grid gap-4 rounded-2xl border border-indigo-100 bg-white p-5 shadow-sm sm:grid-cols-2">
        <h2 className="sm:col-span-2 font-bold text-slate-900">Add a team member</h2>
        <input required placeholder="First name" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} className="input" />
        <input required placeholder="Last name" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} className="input" />
        <input required type="email" placeholder="Work email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input" />
        <input placeholder="Phone (optional)" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="input" />
        <input required minLength={8} type="password" placeholder="Temporary password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="input sm:col-span-2" />
        <div className="flex justify-end gap-2 sm:col-span-2"><button type="button" onClick={() => setOpen(false)} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold">Cancel</button><button disabled={saving} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{saving ? "Adding…" : "Add member"}</button></div>
      </form>}
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-5 py-4"><h2 className="font-bold text-slate-900">{organization?.name || "Company team"}</h2><p className="mt-1 text-sm text-slate-500">{members.length} members · {roles.length} workspace roles</p></div>
        <div className="divide-y divide-slate-100">{members.map((member) => <div key={member.id} className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold text-slate-800">{member.first_name} {member.last_name}</p><p className="text-sm text-slate-500">{member.email}{member.phone ? ` · ${member.phone}` : ""}</p></div><div className="flex items-center gap-3"><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${member.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{member.is_active ? "Active" : "Inactive"}</span><button onClick={() => void remove(member)} className="text-xs font-semibold text-red-600 hover:text-red-700">Remove</button></div></div>)}</div>
        {members.length === 0 && <p className="px-5 py-10 text-center text-sm text-slate-500">No team members found.</p>}
      </section>
    </div>
  );
}
