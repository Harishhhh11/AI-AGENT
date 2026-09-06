# Phase 8 — Company admin dashboard

Phase 8 provides a tenant-scoped company workspace for operating the AI
receptionist platform.

## Dashboard areas

- Dashboard overview with leads, conversations, knowledge, and system status
- AI receptionist (agent) creation, publishing, and public preview
- Knowledge base and document management
- Conversation and lead management
- Company settings for organization name and email
- Team management for adding and removing workspace members

The team and settings screens use the existing authenticated, organization-
scoped `/users`, `/roles`, and `/organizations` APIs. No organization data is
loaded or mutated without the current user's tenant context.
