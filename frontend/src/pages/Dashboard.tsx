import {
  useEffect,
  useState,
} from "react";

import {
  getLeads,
  type Lead,
} from "../api/leads";

import {
  getConversations,
  type Conversation,
} from "../api/conversations";

import {
  getKnowledge,
  type KnowledgeItem,
} from "../api/knowledge";


export default function Dashboard() {
  const [leads, setLeads] =
    useState<Lead[]>([]);

  const [conversations, setConversations] =
    useState<Conversation[]>([]);

  const [knowledge, setKnowledge] =
    useState<KnowledgeItem[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [refreshToken, setRefreshToken] = useState(0);


  useEffect(() => {
    let mounted = true;

    Promise.all([
      getLeads(),
      getConversations(),
      getKnowledge(),
    ])
      .then(
        ([
          leadsData,
          conversationsData,
          knowledgeData,
        ]) => {
          if (!mounted) {
            return;
          }

          setLeads(leadsData);
          setConversations(
            conversationsData
          );
          setKnowledge(
            knowledgeData
          );
        }
      )
      .catch((err: unknown) => {
        if (!mounted) {
          return;
        }

        console.error(
          "Dashboard loading error:",
          err
        );

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load dashboard."
        );
      })
      .finally(() => {
        if (!mounted) {
          return;
        }

        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [refreshToken]);


  const recentLeads = [
    ...leads,
  ]
    .sort(
      (a, b) =>
        b.id - a.id
    )
    .slice(0, 5);


  const recentConversations = [
    ...conversations,
  ]
    .sort(
      (a, b) =>
        b.id - a.id
    )
    .slice(0, 5);


  const activeConversations =
    conversations.filter(
      (conversation) =>
        conversation.status === "active"
    ).length;


  const newLeads =
    leads.filter(
      (lead) =>
        lead.status === "new"
    ).length;


  function formatDate(
    value: string | undefined
  ): string {
    if (!value) {
      return "—";
    }

    const date =
      new Date(value);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return "—";
    }

    return date.toLocaleDateString(
      undefined,
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    );
  }


  function getLeadName(
    lead: Lead
  ): string {
    return (
      lead.name ||
      lead.email ||
      lead.phone ||
      "Unnamed lead"
    );
  }


  function getConversationLabel(
    conversation: Conversation
  ): string {
    return (
      `Conversation #${conversation.id}`
    );
  }


  const cards = [
    {
      title: "Total Leads",
      value: leads.length,
      description:
        `${newLeads} new`,
    },
    {
      title: "Conversations",
      value:
        conversations.length,
      description:
        `${activeConversations} active`,
    },
    {
      title: "Knowledge Items",
      value: knowledge.length,
      description:
        "Company knowledge",
    },
    {
      title: "System Status",
      value: "Online",
      description:
        "AI receptionist operational",
    },
  ];


  return (
    <div className="space-y-6 sm:space-y-8">

      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Workspace overview</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
          Dashboard
        </h1>

        <p className="mt-1 text-sm text-slate-500">
          A live view of conversations, leads, and your AI receptionist.
        </p>
        </div>
        <button type="button" onClick={() => { setLoading(true); setError(null); setRefreshToken((value) => value + 1); }} className="inline-flex w-fit items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-indigo-200 hover:text-indigo-700">
          <span aria-hidden="true">↻</span> Refresh data
        </button>
      </div>


      {/* ================================================== */}
      {/* ERROR */}
      {/* ================================================== */}

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4">

          <p className="text-sm font-medium text-red-700">
            Unable to load dashboard data.
          </p>

          <p className="mt-1 text-sm text-red-600">
            {error}
          </p>

        </div>
      )}


      {/* ================================================== */}
      {/* STAT CARDS */}
      {/* ================================================== */}

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">

        {cards.map(
          (card) => (
            <div
              key={card.title}
              className="group rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_8px_30px_rgba(15,23,42,0.04)] transition hover:-translate-y-0.5 hover:shadow-lg sm:p-6"
            >

              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {card.title}
              </p>

              <p className="mt-3 text-3xl font-bold tracking-tight text-slate-900">

                {loading
                  ? "..."
                  : card.value}

              </p>

              <p className="mt-2 text-xs text-slate-400">
                {loading
                  ? "Loading..."
                  : card.description}
              </p>

            </div>
          )
        )}

      </div>


      {/* ================================================== */}
      {/* SYSTEM + PLATFORM */}
      {/* ================================================== */}

      <div className="grid gap-6 lg:grid-cols-2">

        {/* AI Receptionist */}

        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-[0_8px_30px_rgba(15,23,42,0.04)]">

          <div className="flex items-start justify-between">

            <div>

              <h2 className="font-semibold text-slate-900">
                AI Receptionist
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-500">
                Your AI receptionist is connected to the
                company knowledge base and can handle
                customer conversations and lead capture.
              </p>

            </div>

            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-50 text-green-600">
              ✓
            </span>

          </div>

          <div className="mt-5 flex items-center gap-2">

            <span className="h-2.5 w-2.5 rounded-full bg-green-500" />

            <span className="text-sm font-medium text-green-700">
              Operational
            </span>

          </div>

        </div>


        {/* Platform */}

        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-[0_8px_30px_rgba(15,23,42,0.04)]">

          <h2 className="font-semibold text-slate-900">
            Platform
          </h2>

          <div className="mt-5 space-y-4 text-sm">

            <div className="flex items-center justify-between">

              <span className="text-slate-500">
                AI Model
              </span>

              <span className="font-medium text-slate-900">
                Qwen 2.5 3B
              </span>

            </div>


            <div className="flex items-center justify-between">

              <span className="text-slate-500">
                Vector Search
              </span>

              <span className="font-medium text-slate-900">
                pgvector
              </span>

            </div>


            <div className="flex items-center justify-between">

              <span className="text-slate-500">
                Embeddings
              </span>

              <span className="font-medium text-slate-900">
                MiniLM 384
              </span>

            </div>

          </div>

        </div>

      </div>


      {/* ================================================== */}
      {/* RECENT DATA */}
      {/* ================================================== */}

      <div className="grid gap-6 lg:grid-cols-2">

        {/* Recent Leads */}

        <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_8px_30px_rgba(15,23,42,0.04)]">

          <div className="border-b border-slate-100 px-6 py-5">

            <div className="flex items-center justify-between">

              <div>

                <h2 className="font-semibold text-slate-900">
                  Recent Leads
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  Latest customer enquiries
                </p>

              </div>

              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                {leads.length}
              </span>

            </div>

          </div>


          <div className="divide-y divide-slate-100">

            {loading && (
              <div className="px-6 py-8 text-center text-sm text-slate-400">
                Loading leads...
              </div>
            )}


            {!loading &&
              recentLeads.length === 0 && (
                <div className="px-6 py-8 text-center text-sm text-slate-400">
                  No leads yet.
                </div>
              )}


            {!loading &&
              recentLeads.map(
                (lead) => (
                  <div
                    key={lead.id}
                    className="px-6 py-4"
                  >

                    <div className="flex items-center justify-between gap-4">

                      <div className="min-w-0">

                        <p className="truncate text-sm font-medium text-slate-900">
                          {getLeadName(lead)}
                        </p>

                        <p className="mt-1 truncate text-xs text-slate-500">
                          {lead.interest ||
                            "No interest specified"}
                        </p>

                      </div>


                      <span
                        className={[
                          "shrink-0 rounded-full px-2.5 py-1 text-xs font-medium",
                          lead.status === "new"
                            ? "bg-blue-50 text-blue-700"
                            : "bg-slate-100 text-slate-600",
                        ].join(" ")}
                      >
                        {lead.status}
                      </span>

                    </div>

                  </div>
                )
              )}

          </div>

        </div>


        {/* Recent Conversations */}

        <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_8px_30px_rgba(15,23,42,0.04)]">

          <div className="border-b border-slate-100 px-6 py-5">

            <div className="flex items-center justify-between">

              <div>

                <h2 className="font-semibold text-slate-900">
                  Recent Conversations
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  Latest AI receptionist sessions
                </p>

              </div>

              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                {conversations.length}
              </span>

            </div>

          </div>


          <div className="divide-y divide-slate-100">

            {loading && (
              <div className="px-6 py-8 text-center text-sm text-slate-400">
                Loading conversations...
              </div>
            )}


            {!loading &&
              recentConversations.length === 0 && (
                <div className="px-6 py-8 text-center text-sm text-slate-400">
                  No conversations yet.
                </div>
              )}


            {!loading &&
              recentConversations.map(
                (conversation) => (
                  <div
                    key={conversation.id}
                    className="px-6 py-4"
                  >

                    <div className="flex items-center justify-between gap-4">

                      <div className="min-w-0">

                        <p className="text-sm font-medium text-slate-900">
                          {getConversationLabel(
                            conversation
                          )}
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                          {formatDate(
                            conversation.created_at
                          )}
                        </p>

                      </div>


                      <span
                        className={[
                          "shrink-0 rounded-full px-2.5 py-1 text-xs font-medium",
                          conversation.status ===
                            "active"
                            ? "bg-green-50 text-green-700"
                            : "bg-slate-100 text-slate-600",
                        ].join(" ")}
                      >
                        {conversation.status}
                      </span>

                    </div>

                  </div>
                )
              )}

          </div>

        </div>

      </div>

    </div>
  );
}
