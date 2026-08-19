import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { sendMessage } from "../api/chat";

interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
}

const WELCOME_MESSAGE =
  "Hello! Welcome to Maruthi Technologies. How can I help you today?";

const SUGGESTED_PROMPTS = [
  "Which courses do you offer?",
  "What are the course fees?",
  "I want to join a course",
];

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: 1, role: "assistant", content: WELCOME_MESSAGE },
  ]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(
    () => localStorage.getItem("chat_session_id")
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = input.trim();

    if (!message || loading) return;

    setError(null);
    setMessages((previous) => [
      ...previous,
      { id: Date.now(), role: "user", content: message },
    ]);
    setInput("");
    setLoading(true);

    try {
      const result = await sendMessage(message, sessionId);

      if (result.session_id) {
        setSessionId(result.session_id);
        localStorage.setItem("chat_session_id", result.session_id);
      }

      setMessages((previous) => [
        ...previous,
        { id: Date.now() + 1, role: "assistant", content: result.response },
      ]);
    } catch (err) {
      console.error("Chat error:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to contact the AI receptionist."
      );
    } finally {
      setLoading(false);
      window.setTimeout(() => inputRef.current?.focus(), 0);
    }
  }

  function startNewConversation() {
    localStorage.removeItem("chat_session_id");
    setSessionId(null);
    setMessages([{ id: Date.now(), role: "assistant", content: WELCOME_MESSAGE }]);
    setInput("");
    setError(null);
    window.setTimeout(() => inputRef.current?.focus(), 0);
  }

  return (
    <div className="flex min-h-[calc(100dvh-9rem)] flex-col gap-5 sm:gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Live assistant</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">AI Receptionist</h1>
          <p className="mt-1 text-sm text-slate-500">Test the exact experience your customers receive.</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700">
            <span className="h-2 w-2 rounded-full bg-emerald-500" /> AI online
          </span>
          <button type="button" onClick={startNewConversation} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-indigo-200 hover:text-indigo-700">
            New chat
          </button>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_12px_40px_rgba(15,23,42,0.06)]">
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/70 px-5 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-sm font-bold text-white">AI</div>
            <div>
              <p className="text-sm font-semibold text-slate-900">Receptionist preview</p>
              <p className="text-xs text-slate-500">Knowledge-aware customer assistant</p>
            </div>
          </div>
          <span className="hidden text-xs text-slate-400 sm:block">{sessionId ? "Active session" : "New session"}</span>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto bg-[linear-gradient(180deg,#f8fafc_0%,#ffffff_45%)] p-4 sm:p-6">
          <div className="mx-auto max-w-3xl space-y-5">
            {messages.map((message) => {
              const isUser = message.role === "user";
              return (
                <div key={message.id} className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
                  {!isUser && <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-[10px] font-bold text-white">AI</div>}
                  <div className={`max-w-[88%] sm:max-w-[75%] ${isUser ? "items-end" : "items-start"}`}>
                    <p className={`mb-1 px-1 text-[11px] font-medium ${isUser ? "text-right text-slate-400" : "text-slate-400"}`}>{isUser ? "You" : "AI Receptionist"}</p>
                    <div className={isUser ? "rounded-2xl rounded-br-md bg-indigo-600 px-4 py-3 text-sm leading-6 text-white shadow-sm" : "rounded-2xl rounded-bl-md border border-slate-100 bg-white px-4 py-3 text-sm leading-6 text-slate-700 shadow-sm"}>
                      {message.content}
                    </div>
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex items-start gap-3">
                <div className="mt-1 flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-[10px] font-bold text-white">AI</div>
                <div className="rounded-2xl rounded-bl-md border border-slate-100 bg-white px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-1.5" aria-label="AI receptionist is typing">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:150ms]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {messages.length === 1 && !loading && (
          <div className="border-t border-slate-100 px-4 py-3 sm:px-6">
            <p className="mb-2 text-xs font-medium text-slate-500">Try a quick question</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button type="button" key={prompt} onClick={() => { setInput(prompt); inputRef.current?.focus(); }} className="rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-700 transition hover:bg-indigo-100">
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {error && <div className="border-t border-red-100 bg-red-50 px-5 py-3 text-sm text-red-700" role="alert">{error}</div>}

        <form onSubmit={handleSubmit} className="border-t border-slate-200 bg-white p-3 sm:p-4">
          <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-1.5 transition focus-within:border-indigo-400 focus-within:bg-white focus-within:ring-4 focus-within:ring-indigo-500/10">
            <input ref={inputRef} type="text" value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask about courses, pricing, admissions, or services..." disabled={loading} className="min-w-0 flex-1 bg-transparent px-3 py-2.5 text-sm text-slate-800 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed" aria-label="Message to AI receptionist" />
            <button type="submit" disabled={loading || !input.trim()} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50 sm:px-5">
              {loading ? "Sending" : "Send"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
