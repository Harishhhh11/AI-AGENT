import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getConversations,
  getMessages,
  updateConversationStatus,
} from "../api/conversations";

import type {
  Conversation,
  Message,
} from "../api/conversations";


const statuses = [
  "all",
  "active",
  "closed",
];


export default function Conversations() {
  const [
    conversations,
    setConversations,
  ] = useState<Conversation[]>([]);

  const [
    selectedConversationId,
    setSelectedConversationId,
  ] = useState<number | null>(null);

  const [
    messages,
    setMessages,
  ] = useState<Message[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    messagesLoading,
    setMessagesLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    statusFilter,
    setStatusFilter,
  ] = useState("all");

  const [
    updatingStatus,
    setUpdatingStatus,
  ] = useState(false);

  const [
    refreshToken,
    setRefreshToken,
  ] = useState(0);


  /*
   * Load conversations.
   *
   * We intentionally do not automatically select the first
   * conversation here. The user can select one from the list.
   */
  useEffect(() => {
    let cancelled = false;

    async function loadConversations() {
      try {
        const data =
          await getConversations();

        if (cancelled) {
          return;
        }

        setConversations(data);
      } catch (err) {
        console.error(
          "Unable to load conversations:",
          err
        );

        if (!cancelled) {
          setError(
            "Unable to load conversations."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadConversations();

    return () => {
      cancelled = true;
    };
  }, [refreshToken]);


  /*
   * Currently selected conversation.
   */
  const selectedConversation =
    useMemo(
      () => {
        if (
          selectedConversationId === null
        ) {
          return null;
        }

        return (
          conversations.find(
            (conversation) =>
              conversation.id ===
              selectedConversationId
          ) ?? null
        );
      },
      [
        conversations,
        selectedConversationId,
      ]
    );


  /*
   * Filter conversations.
   */
  const filteredConversations =
    useMemo(() => {
      const searchValue =
        search
          .trim()
          .toLowerCase();

      return conversations.filter(
        (conversation) => {
          const matchesStatus =
            statusFilter === "all" ||
            conversation.status ===
              statusFilter;

          if (!matchesStatus) {
            return false;
          }

          if (!searchValue) {
            return true;
          }

          return (
            String(
              conversation.id
            ).includes(searchValue) ||
            conversation.session_id
              .toLowerCase()
              .includes(searchValue) ||
            conversation.status
              .toLowerCase()
              .includes(searchValue)
          );
        }
      );
    }, [
      conversations,
      search,
      statusFilter,
    ]);


  /*
   * Select conversation and load messages.
   */
  async function selectConversation(
    conversation: Conversation
  ) {
    try {
      setSelectedConversationId(
        conversation.id
      );

      setMessages([]);

      setMessagesLoading(true);

      setError("");

      const data =
        await getMessages(
          conversation.id
        );

      setMessages(data);
    } catch (err) {
      console.error(
        "Unable to load messages:",
        err
      );

      setError(
        "Unable to load conversation messages."
      );
    } finally {
      setMessagesLoading(false);
    }
  }


  /*
   * Update conversation status.
   */
  async function changeStatus(
    newStatus: string
  ) {
    if (
      selectedConversation === null ||
      updatingStatus
    ) {
      return;
    }

    try {
      setUpdatingStatus(true);

      setError("");

      const updated =
        await updateConversationStatus(
          selectedConversation.id,
          newStatus
        );

      setConversations(
        (current) =>
          current.map(
            (conversation) =>
              conversation.id ===
              updated.id
                ? updated
                : conversation
          )
      );
    } catch (err) {
      console.error(
        "Unable to update conversation status:",
        err
      );

      setError(
        "Unable to update conversation status."
      );
    } finally {
      setUpdatingStatus(false);
    }
  }


  /*
   * Format date.
   */
  function formatDate(
    value: string
  ): string {
    const date =
      new Date(value);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return value;
    }

    return date.toLocaleString();
  }


  /*
   * Status styling.
   */
  function statusClass(
    status: string
  ): string {
    switch (status) {
      case "active":
        return "bg-green-50 text-green-700";

      case "closed":
        return "bg-slate-100 text-slate-600";

      default:
        return "bg-blue-50 text-blue-700";
    }
  }


  return (
    <div className="flex min-h-[calc(100dvh-9rem)] flex-col">

      {/* =====================================================
          HEADER
          ===================================================== */}

      <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">

        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">
            Customer activity
          </p>
        <h1 className="text-2xl font-bold text-slate-900">
          Conversations
        </h1>

        <p className="mt-1 text-sm text-slate-500">
          Review conversations handled by your AI receptionist.
        </p>
        </div>

        <button
          type="button"
          onClick={() => {
            setLoading(true);
            setError("");
            setRefreshToken((value) => value + 1);
          }}
          className="inline-flex w-fit items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-indigo-200 hover:text-indigo-700"
        >
          <span aria-hidden="true">↻</span> Refresh
        </button>

      </div>


      {/* =====================================================
          ERROR
          ===================================================== */}

      {error && (
        <div className="mb-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}


      {/* =====================================================
          MAIN
          ===================================================== */}

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_12px_40px_rgba(15,23,42,0.06)] lg:flex-row">


        {/* ===================================================
            LEFT SIDE
            =================================================== */}

        <aside className="flex max-h-[26rem] w-full shrink-0 flex-col border-b border-slate-200 bg-slate-50/40 lg:max-h-none lg:w-80 lg:border-b-0 lg:border-r">


          {/* Search / Filter */}

          <div className="space-y-3 border-b border-slate-200 p-4">

            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">All conversations</p>
              <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-semibold text-indigo-700">{conversations.length}</span>
            </div>

            <input
              value={search}
              onChange={(event) =>
                setSearch(
                  event.target.value
                )
              }
              placeholder="Search conversations..."
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
            />


            <select
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(
                  event.target.value
                )
              }
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
            >

              {statuses.map(
                (status) => (
                  <option
                    key={status}
                    value={status}
                  >
                    {status ===
                    "all"
                      ? "All statuses"
                      : status
                          .charAt(0)
                          .toUpperCase() +
                        status.slice(1)}
                  </option>
                )
              )}

            </select>

          </div>


          {/* Conversation list */}

          <div className="min-h-0 flex-1 overflow-y-auto">

            {loading ? (

              <div className="p-6 text-center">

                <div className="mx-auto h-7 w-7 animate-spin rounded-full border-2 border-slate-200 border-t-slate-700" />

                <p className="mt-3 text-sm text-slate-500">
                  Loading conversations...
                </p>

              </div>

            ) : filteredConversations.length ===
              0 ? (

              <div className="p-6 text-center">

                <div className="text-3xl">
                  💬
                </div>

                <p className="mt-3 font-medium text-slate-700">
                  No conversations found
                </p>

                <p className="mt-1 text-xs leading-5 text-slate-400">
                  Conversations will appear here
                  when customers interact with the
                  receptionist.
                </p>

              </div>

            ) : (

              filteredConversations.map(
                (conversation) => {

                  const active =
                    selectedConversationId ===
                    conversation.id;

                  return (
                    <button
                      type="button"
                      key={
                        conversation.id
                      }
                      onClick={() =>
                        void selectConversation(
                          conversation
                        )
                      }
                      className={`w-full border-b border-slate-100 px-4 py-4 text-left transition ${
                        active
                          ? "bg-indigo-50 shadow-[inset_3px_0_0_#4f46e5]"
                          : "hover:bg-white"
                      }`}
                    >

                      <div className="flex items-center justify-between gap-2">

                        <p className="font-medium text-slate-900">
                          Conversation #
                          {
                            conversation.id
                          }
                        </p>

                        <span
                          className={`shrink-0 rounded-full px-2 py-1 text-[10px] font-medium uppercase ${statusClass(
                            conversation.status
                          )}`}
                        >
                          {
                            conversation.status
                          }
                        </span>

                      </div>


                      <p className="mt-1 truncate text-xs text-slate-400">
                        Session:{" "}
                        {
                          conversation.session_id
                        }
                      </p>


                      <p className="mt-2 text-xs text-slate-400">
                        {formatDate(
                          conversation.updated_at
                        )}
                      </p>

                    </button>
                  );
                }
              )

            )}

          </div>

        </aside>


        {/* ===================================================
            RIGHT SIDE
            =================================================== */}

        <section className="flex min-h-[32rem] min-w-0 flex-1 flex-col bg-white">


          {/* No conversation selected */}

          {selectedConversation ===
          null ? (

            <div className="flex flex-1 items-center justify-center">

              <div className="text-center">

                <div className="text-5xl">
                  💬
                </div>

                <h2 className="mt-4 font-semibold text-slate-800">
                  Select a conversation
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Choose a conversation from
                  the list to view its messages.
                </p>

              </div>

            </div>

          ) : (

            <>

              {/* =============================================
                  CONVERSATION HEADER
                  ============================================= */}

              <div className="border-b border-slate-200 bg-white px-5 py-4 sm:px-6">

                <div className="flex items-center justify-between gap-4">

                  <div className="min-w-0">

                    <h2 className="font-semibold text-slate-900">
                      Conversation #
                      {
                        selectedConversation.id
                      }
                    </h2>

                    <p className="mt-1 truncate text-xs text-slate-400">
                      Session ID:{" "}
                      {
                        selectedConversation.session_id
                      }
                    </p>

                  </div>


                  <select
                    value={
                      selectedConversation.status
                    }
                    disabled={
                      updatingStatus
                    }
                    onChange={(event) =>
                      void changeStatus(
                        event.target.value
                      )
                    }
                    className={`rounded-full border-0 px-3 py-1.5 text-xs font-medium outline-none ${statusClass(
                      selectedConversation.status
                    )}`}
                  >

                    <option value="active">
                      Active
                    </option>

                    <option value="closed">
                      Closed
                    </option>

                  </select>

                </div>

              </div>


              {/* =============================================
                  MESSAGES
                  ============================================= */}

              <div className="min-h-0 flex-1 overflow-y-auto bg-[linear-gradient(180deg,#f8fafc_0%,#ffffff_45%)] p-4 sm:p-6">

                {messagesLoading ? (

                  <div className="flex h-full items-center justify-center">

                    <div className="text-center">

                      <div className="mx-auto h-7 w-7 animate-spin rounded-full border-2 border-slate-200 border-t-slate-700" />

                      <p className="mt-3 text-sm text-slate-500">
                        Loading messages...
                      </p>

                    </div>

                  </div>

                ) : messages.length ===
                  0 ? (

                  <div className="flex h-full items-center justify-center">

                    <div className="text-center">

                      <div className="text-4xl">
                        💬
                      </div>

                      <p className="mt-3 font-medium text-slate-700">
                        No messages
                      </p>

                      <p className="mt-1 text-sm text-slate-400">
                        This conversation does
                        not contain any messages yet.
                      </p>

                    </div>

                  </div>

                ) : (

                  <div className="mx-auto max-w-3xl space-y-5">

                    {messages.map(
                      (message) => {

                        const isUser =
                          message.role ===
                          "user";

                        return (
                          <div
                            key={
                              message.id
                            }
                            className={`flex ${
                              isUser
                                ? "justify-end"
                                : "justify-start"
                            }`}
                          >

                            <div className="max-w-[75%]">

                              <div className="mb-1 px-1 text-[11px] font-medium uppercase tracking-wide text-slate-400">

                                {isUser
                                  ? "Customer"
                                  : "AI Receptionist"}

                              </div>


                              <div
                                className={`rounded-2xl px-4 py-3 text-sm leading-6 ${
                                  isUser
                                    ? "rounded-br-sm bg-indigo-600 text-white shadow-sm"
                                    : "rounded-bl-sm border border-slate-200 bg-white text-slate-700 shadow-sm"
                                }`}
                              >
                                {
                                  message.content
                                }
                              </div>


                              <div
                                className={`mt-1 px-1 text-[10px] text-slate-400 ${
                                  isUser
                                    ? "text-right"
                                    : "text-left"
                                }`}
                              >
                                {formatDate(
                                  message.created_at
                                )}
                              </div>

                            </div>

                          </div>
                        );
                      }
                    )}

                  </div>

                )}

              </div>


              {/* =============================================
                  FOOTER
                  ============================================= */}

              <div className="border-t border-slate-200 bg-white px-6 py-3">

                <p className="text-center text-xs text-slate-400">
                  Conversation history is read-only.
                </p>

              </div>

            </>

          )}

        </section>

      </div>

    </div>
  );
}
