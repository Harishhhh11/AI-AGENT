# Phase 7 — Lead capture acceptance

Lead capture is deliberately deterministic. `LeadContextService` detects
business intent, extracts only customer-provided values, validates phone and
email answers, and asks for missing fields in this order:

1. interest
2. name
3. phone
4. email

`ChatService` runs this state machine before the LLM. Conversation history is
rehydrated from the organization-scoped lead row, so the flow survives a
short history window or a process restart. Saving a context is an
organization-scoped upsert by conversation, phone, or email. Database
uniqueness constraints provide a final duplicate-prevention guard.

Public chat resolves an active, published agent from its slug before creating
the conversation. Session IDs cannot be reused across organizations or
agents. Protected lead and conversation APIs always scope reads and writes to
the authenticated organization.

If the LLM is unavailable, deterministic lead capture and verified
knowledge-safe responses continue to work; ordinary free-form requests return
a bounded apology rather than an invented answer. Run the backend regression
suite from `backend/` with `pytest`.
