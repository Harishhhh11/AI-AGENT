# AI Receptionist Platform V2 — Completion Roadmap

This roadmap is the acceptance contract for the complete platform upgrade.

## Product goal

Build a dependable multi-tenant AI receptionist platform that can be configured by a business owner, grounded in its own knowledge, capture and qualify leads, operate across supported channels, and provide an excellent operator dashboard.

## AI conversation quality

- Hybrid lexical + semantic retrieval with deterministic ranking.
- Subject continuity across multi-turn conversations.
- Explicit topic switching without leaking facts from the previous topic.
- Company-wide questions can aggregate multiple relevant knowledge items.
- Follow-up questions inherit the active subject when appropriate.
- Unknown subjects must produce an honest knowledge-gap response.
- Verified knowledge is authoritative for company facts.
- LLM is used for natural synthesis, never for tenant selection or factual invention.
- Long answers preserve important lists, steps, numbers, and caveats.
- Multiple questions are answered independently in one response.
- Lead capture remains deterministic and persistent.
- Invalid lead fields do not corrupt previously captured fields.
- Tool actions remain behind the tool registry/orchestrator.

## Admin product

- Agent/receptionist creation, editing, publishing, preview, and testing.
- Agent-specific knowledge assignment plus organization-wide shared knowledge.
- Knowledge CRUD with source/category/status visibility.
- Documents ingestion with clear processing state and failure feedback.
- Leads list, detail, status, filtering, and search.
- Conversation list, search, detail, and transcript review.
- Analytics with useful operational KPIs.
- Integrations status and configuration surfaces.
- Team and settings management.
- Responsive navigation and consistent design system.
- Loading, empty, success, error, and offline states for every major surface.

## Public experience

- Published agent resolves safely from its public slug.
- Clean branded chat experience.
- Persistent session continuity.
- Mobile-first layout.
- Clear typing/loading state and retry path.

## Reliability

- Tenant isolation tests.
- Public-agent isolation tests.
- Retrieval regression suite.
- Lead-state regression suite.
- API contract tests.
- Frontend lint/build checks.
- CI must be green before merge.

## Completion gate

The upgrade is complete only when the implementation, regression tests, frontend build, CI checks, and end-to-end chat acceptance scenarios are all green.