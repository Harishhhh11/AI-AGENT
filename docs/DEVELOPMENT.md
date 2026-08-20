# AI Receptionist Platform — Development Guide

## Source of truth

GitHub is the source of truth for the project. Work on feature branches and merge only after tests pass.

## Branching

- `main`: stable baseline
- `phase-*/*`: phase work
- `feature/*`: isolated feature work
- `fix/*`: focused bug fixes

Never commit secrets, `.env` files, local databases, virtual environments, or generated build output.

## Backend

Run from `backend/`:

```bash
pytest
```

Local API:

```bash
uvicorn app.main:app --reload
```

## Frontend

Run from `frontend/`:

```bash
npm install
npm run dev
npm run lint
npm run build
```

## Architecture rules

1. Company-specific facts belong in organization/agent knowledge, not Python constants in service logic.
2. Every tenant-scoped read/write must use `organization_id` or an agent that is already verified to belong to that organization.
3. Public APIs must resolve the published agent before creating or continuing anonymous conversations.
4. Conversation state must be deterministic for structured workflows such as lead capture.
5. LLM output must not be treated as authoritative for validation, permissions, tenant selection, or database identity.
6. External actions must go through the tool registry/orchestrator.
7. Database schema changes require Alembic migrations.
8. New behavior should have regression tests before the feature is considered complete.

## Phase 0 goal

Establish a runnable, testable baseline before larger SaaS features are added.