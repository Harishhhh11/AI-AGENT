import { Component, useEffect, useRef, useState } from "react";
import type { ErrorInfo, ReactNode } from "react";
import type { FormEvent } from "react";
import { useParams } from "react-router-dom";

import { getPublicAgent, sendPublicMessage } from "../api/publicChat";
import type { PublicAgent } from "../api/publicChat";

type Message = { id: number; role: "user" | "assistant"; content: string };

export default function PublicChat() {
  return <PublicChatErrorBoundary><PublicChatInterface /></PublicChatErrorBoundary>;
}

function PublicChatInterface() {
  const { slug = "" } = useParams();
  const storageKey = `public_chat_session:${slug}`;
  const [agent, setAgent] = useState<PublicAgent | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(() => localStorage.getItem(storageKey));
  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    void getPublicAgent(slug)
      .then((value) => {
        if (cancelled) return;
        setAgent(value);
        setMessages([{ id: Date.now(), role: "assistant", content: value.welcome_message }]);
      })
      .catch((reason: unknown) => !cancelled && setError(reason instanceof Error ? reason.message : "Unable to load this receptionist."))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [slug]);

  // Do not implicitly return the result of scrollIntoView. React treats an
  // effect return value as a cleanup function; some browser implementations
  // return a non-function value here, causing "destroy is not a function".
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = input.trim();
    if (!text || sending || !agent) return;
    setMessages((current) => [...current, { id: Date.now(), role: "user", content: text }]);
    setInput(""); setError(""); setSending(true);
    try {
      const result = await sendPublicMessage(slug, text, sessionId);
      if (typeof result.session_id !== "string" || typeof result.response !== "string") {
        throw new Error("The receptionist returned an invalid response. Please try again.");
      }
      setSessionId(result.session_id);
      try {
        localStorage.setItem(storageKey, result.session_id);
      } catch {
        // Chat continues even when browser storage is unavailable.
      }
      setMessages((current) => [...current, { id: Date.now() + 1, role: "assistant", content: String(result.response) }]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to send your message.");
    } finally { setSending(false); }
  }

  if (loading) return <main className="grid min-h-screen place-items-center bg-slate-950 text-sm font-medium text-slate-300">Loading assistant…</main>;
  if (error && !agent) return <main className="grid min-h-screen place-items-center bg-slate-950 px-6 text-center"><div><p className="text-xl font-bold text-white">Receptionist unavailable</p><p className="mt-2 text-sm text-slate-400">{error}</p></div></main>;

  return <main className="min-h-screen bg-slate-950 p-4 sm:grid sm:place-items-center sm:p-8">
    <section className="flex min-h-[calc(100dvh-2rem)] w-full max-w-3xl flex-col overflow-hidden rounded-3xl border border-white/10 bg-white shadow-2xl sm:min-h-[680px]">
      <header className="flex items-center gap-3 bg-gradient-to-r from-indigo-700 to-violet-700 px-5 py-4 text-white">
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-white/15 font-bold">AI</div>
        <div><h1 className="font-bold">{agent?.name}</h1><p className="text-xs text-indigo-100">Online now · AI receptionist</p></div>
      </header>
      <div className="flex-1 space-y-5 overflow-y-auto bg-slate-50 p-5 sm:p-7">
        {messages.map((message) => <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}><div className={`max-w-[82%] rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm ${message.role === "user" ? "rounded-br-md bg-indigo-600 text-white" : "rounded-bl-md border border-slate-100 bg-white text-slate-700"}`}>{message.content}</div></div>)}
        {sending && <div className="w-fit rounded-2xl rounded-bl-md bg-white px-4 py-3 text-sm text-slate-500 shadow-sm">Thinking…</div>}
        <div ref={endRef} />
      </div>
      {error && <p className="border-t border-red-100 bg-red-50 px-5 py-3 text-sm text-red-700">{error}</p>}
      <form onSubmit={submit} className="border-t border-slate-200 p-3"><div className="flex gap-2 rounded-2xl bg-slate-100 p-1.5"><input value={input} onChange={(event) => setInput(event.target.value)} disabled={sending} placeholder="Type your message…" className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm outline-none" /><button disabled={sending || !input.trim()} className="rounded-xl bg-indigo-600 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50">Send</button></div></form>
    </section>
  </main>;
}

class PublicChatErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean; message: string }> {
  state = { failed: false, message: "" };

  static getDerivedStateFromError(error: Error) {
    return { failed: true, message: error.message || "An unexpected rendering error occurred." };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Public chat interface error:", error, info);
  }

  render() {
    if (this.state.failed) {
      return <main className="grid min-h-screen place-items-center bg-slate-950 px-6 text-center"><div><p className="text-xl font-bold text-white">Unable to display the chat</p><p className="mt-2 text-sm text-slate-400">{this.state.message}</p><button type="button" onClick={() => window.location.reload()} className="mt-5 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white">Refresh chat</button></div></main>;
    }
    return this.props.children;
  }
}
