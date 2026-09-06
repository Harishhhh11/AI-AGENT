# Phase 9 — Analytics

Phase 9 adds organization-scoped performance intelligence for the company
admin dashboard.

## Included metrics

- Conversation totals, active/completed counts, and average messages
- Message totals and user/assistant activity
- Lead totals, new leads, qualified leads, and converted leads
- Conversion rate based on converted leads per conversation
- Popular customer questions ranked by frequency
- Unanswered questions detected from missing or uncertain assistant replies

Analytics are served by `GET /api/v1/analytics/overview` and are restricted
to the authenticated user's organization. The frontend exposes the data at
the new Analytics dashboard route.
