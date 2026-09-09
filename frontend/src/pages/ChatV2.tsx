import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { getAgent, getAgents } from "../api/agents";
import type { Agent } from "../api/agents";
import { sendMessage } from "../api/chat";
import PageHeader from "../components/common/PageHeader";
import StatusBadge from "../components/common/StatusBadge";

interface ChatMessage { id: number; role: "user" | "assistant"; content: string; }

const FALLBACK_WELCOME = "Hello! How can I help you today?";
const SUGGESTED = [
  "Which courses do you offer?",
  "What topics are covered?",
  "What are the fees?",
  "Can I join online?",
];

export default function ChatV2() {
  const { agentId: agentIdParam } = useParams();
  const routeAgentId = agentIdParam ? Number(agentIdParam) : null;
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(routeAgentId && Number.isInteger(routeAgentId) ? routeAgentId : null);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingAgent, setLoadingAgent] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<number | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    let mounted = true;
    void getAgents()
      .then((items) => {
        if (!mounted) return;
        setAgents(items);
        const initialId = routeAgentId && items.some((item) => item.id === routeAgentId)
          ? routeAgentId
          : items[0]?.id ?? null;
        setSelectedAgentId(initialId);
      })
      .catch((reason) => {
        if (mounted) setError(reason instanceof Error ? reason.message : "Unable to load your receptionists.");
      })
      .finally(() => {
        if (mounted) setLoadingAgent(false);
      });
    return () => { mounted = false; };
  }, [routeAgentId]);

  useEffect(() => {
    let mounted = true;
    if (!selectedAgentId) {
      setAgent(null);
      setMessages([{ id: Date.now(), role: "assistant", content: FALLBACK_WELCOME }]);
      setSessionId(null);
      return () => { mounted = false; };
    }
    setLoadingAgent(true);
    setError(null);
    const storageKey = `chat_session:${selectedAgentId}`;
    const savedSession = localStorage.getItem(storageKey);
    void getAgent(selectedAgentId)
      .then((value) => {
        if (!mounted) return;
        setAgent(value);
        setMessages([{ id: Date.now(), role: "assistant", content: value.welcome_message || FALLBACK_WELCOME }]);
        setSessionId(savedSession);
      })
      .catch((reason) => {
        if (mounted) setError(reason instanceof Error ? reason.message : "Unable to load this receptionist.");
      })
      .finally(() => {
        if (mounted) setLoadingAgent(false);
      });
    return () => { mounted = false; };
  }, [selectedAgentId]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  function selectAgent(value: number) {
    setSelectedAgentId(value);
    setInput("");
    setError(null);
  }

  async function submit(message: string) {
    const text = message.trim();
    if (!text || loading || !selectedAgentId) return;
    setError(null); setInput(""); setLoading(true);
    setMessages((prev) => [...prev, { id: Date.now(), role: "user", content: text }]);
    try {
      const result = await sendMessage(text, sessionId, selectedAgentId);
      if (result.session_id) {
        setSessionId(result.session_id);
        localStorage.setItem(`chat_session:${selectedAgentId}`, result.session_id);
      }
      setMessages((prev) => [...prev, { id: Date.now() + 1, role: "assistant", content: result.response }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to contact the AI receptionist.");
    } finally {
      setLoading(false);
      window.setTimeout(() => inputRef.current?.focus(), 0);
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); await submit(input); }

  function newChat() {
    if (selectedAgentId) localStorage.removeItem(`chat_session:${selectedAgentId}`);
    setSessionId(null);
    setMessages([{ id: Date.now(), role: "assistant", content: agent?.welcome_message || FALLBACK_WELCOME }]);
    setError(null); setInput("");
  }

  async function copy(text: string, id: number) {
    try { await navigator.clipboard.writeText(text); setCopied(id); window.setTimeout(() => setCopied(null), 1200); }
    catch { setError("Unable to copy response."); }
  }

  if (loadingAgent && agents.length === 0) {
    return <div className="space-y-6"><PageHeader eyebrow="Receptionist tester" title="Test your receptionists" description="Choose a configured receptionist and test exactly the knowledge assigned to it." /><div className="card p-10 text-center text-sm text-slate-500">Loading receptionists…</div></div>;
  }

  return <div className="space-y-6">
    <PageHeader
      eyebrow="Receptionist tester"
      title={agent ? agent.name : "Test your receptionists"}
      description={agent ? "Every message is routed to this receptionist and its own knowledge scope." : "Choose a configured receptionist to start testing."}
      actions={<div className="flex items-center gap-2"><StatusBadge label="AI online" tone="green" /><button type="button" onClick={newChat} disabled={!selectedAgentId} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm hover:border-indigo-200 hover:text-indigo-700 disabled:opacity-50">New chat</button></div>}
    />

    {error && <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">{error}</div>}

    <div className="grid gap-5 xl:grid-cols-[280px_minmax(0,1fr)]">
      <aside className="card p-4">
        <div className="flex items-center justify-between"><div><p className="text-[11px] font-bold uppercase tracking-[0.18em] text-indigo-600">Your Receptionists</p><p className="mt-1 text-xs text-slate-500">Test one at a time</p></div><Link to="/agents" className="text-xs font-semibold text-indigo-700">Manage</Link></div>
        <div className="mt-4 space-y-2">
          {agents.map((item) => (
            <button key={item.id} type="button" onClick={() => selectAgent(item.id)} className={`w-full rounded-xl border px-3 py-3 text-left transition ${selectedAgentId === item.id ? "border-indigo-200 bg-indigo-50" : "border-slate-200 bg-white hover:border-indigo-100 hover:bg-slate-50"}`}>
              <div className="flex items-center justify-between gap-2"><p className="truncate text-sm font-semibold text-slate-900">{item.name}</p><span className={`h-2 w-2 shrink-0 rounded-full ${item.is_active ? "bg-emerald-500" : "bg-slate-300"}`} /></div>
              <p className="mt-1 text-xs text-slate-500">{item.knowledge_item_ids?.length ?? 0} private knowledge items</p>
            </button>
          ))}
          {agents.length === 0 && <div className="rounded-xl bg-slate-50 p-4 text-xs leading-5 text-slate-500">Create your first receptionist, select knowledge during setup, then return here to test it.</div>}
        </div>
      </aside>

      <section className="flex min-h-[620px] flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-[0_20px_60px_rgb(15_23_42_/_0.06)]">
        <header className="flex items-center justify-between border-b border-slate-100 px-5 py-4 sm:px-6"><div className="flex items-center gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-sm font-black text-white">AI</div><div><p className="text-sm font-semibold text-slate-950">{agent?.name || "No receptionist selected"}</p><p className="text-xs text-slate-500">{agent ? `${agent.knowledge_item_ids?.length ?? 0} selected knowledge items` : "Create a receptionist to begin"}</p></div></div><div className="text-right"><p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Session</p><p className="mt-1 text-xs font-semibold text-slate-700">{sessionId ? "Active" : "New"}</p></div></header>
        <div className="app-scrollbar flex-1 overflow-y-auto bg-[linear-gradient(180deg,#f8fafc_0%,#fff_55%)] p-4 sm:p-6"><div className="mx-auto max-w-3xl space-y-6">{messages.map((message) => <div key={message.id} className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}>{message.role === "assistant" && <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-[10px] font-bold text-white">AI</div>}<div className="max-w-[90%] sm:max-w-[82%]"><p className={`mb-1 px-1 text-[10px] font-semibold uppercase tracking-wide ${message.role === "user" ? "text-right text-slate-400" : "text-slate-400"}`}>{message.role === "user" ? "You" : agent?.name || "AI Receptionist"}</p><div className={message.role === "user" ? "rounded-2xl rounded-br-md bg-indigo-600 px-4 py-3 text-sm leading-6 text-white shadow-sm" : "group rounded-2xl rounded-bl-md border border-slate-100 bg-white px-4 py-3 text-sm leading-6 text-slate-700 shadow-sm"}><div className="whitespace-pre-wrap">{message.content}</div>{message.role === "assistant" && <button type="button" onClick={() => copy(message.content, message.id)} className="mt-3 text-[11px] font-semibold text-slate-400 opacity-0 transition group-hover:opacity-100 hover:text-indigo-600">{copied === message.id ? "Copied" : "Copy response"}</button>}</div></div></div>)}{loading && <div className="flex gap-3"><div className="mt-1 flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-[10px] font-bold text-white">AI</div><div className="rounded-2xl rounded-bl-md border border-slate-100 bg-white px-4 py-3 shadow-sm"><div className="flex gap-1.5"><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400"/><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:150ms]"/><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:300ms]"/></div></div></div>}<div ref={endRef}/></div></div>
        {messages.length === 1 && !loading && selectedAgentId && <div className="border-t border-slate-100 px-4 py-4 sm:px-6"><p className="mb-2 text-xs font-semibold text-slate-500">Suggested questions</p><div className="flex flex-wrap gap-2">{SUGGESTED.map((item) => <button key={item} type="button" onClick={() => void submit(item)} className="rounded-full border border-indigo-100 bg-indigo-50 px-3 py-2 text-xs font-semibold text-indigo-700 hover:bg-indigo-100">{item}</button>)}</div></div>}
        <form onSubmit={onSubmit} className="border-t border-slate-200 bg-white p-3 sm:p-4"><div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-1.5 focus-within:border-indigo-400 focus-within:bg-white focus-within:ring-4 focus-within:ring-indigo-500/10"><input ref={inputRef} value={input} onChange={(e) => setInput(e.target.value)} disabled={loading || !selectedAgentId} placeholder={selectedAgentId ? "Ask about this receptionist's knowledge…" : "Select a receptionist first"} className="min-w-0 flex-1 bg-transparent px-3 py-2.5 text-sm outline-none placeholder:text-slate-400" /><button type="submit" disabled={loading || !input.trim() || !selectedAgentId} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">{loading ? "Thinking…" : "Send"}</button></div></form>
      </section>
    </div>
  </div>;
}
