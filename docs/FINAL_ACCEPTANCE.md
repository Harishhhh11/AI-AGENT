# Final Acceptance Gate

## Purpose

This checklist defines the final production-readiness gate for the AI Receptionist Platform.

## Completed architecture gates

- Ollama-first semantic conversation orchestration
- Grounded, organization/agent-scoped knowledge retrieval
- Multi-intent question decomposition and synthesis
- Deterministic lead workflow handling
- Tool orchestration separated from model authority
- Tenant isolation regression coverage
- Backend/frontend/API/integration/security CI coverage
- Production deployment hardening and observability endpoints

## Runtime acceptance required before release

1. Start PostgreSQL/pgvector, backend, frontend, and Ollama using the documented deployment path.
2. Load representative organization and receptionist knowledge.
3. Verify direct factual questions and paraphrases for fees, duration, timings, topics, mode, eligibility, payment, certificate, and course catalog.
4. Verify follow-ups retain the intended subject without leaking information across courses.
5. Verify multi-intent requests answer every supported request and clearly report unavailable facts.
6. Verify typo/colloquial inputs fall back safely when Ollama is unavailable.
7. Verify anonymous/public-agent conversations cannot cross organization or agent boundaries.
8. Verify lead capture remains deterministic and persists correctly across conversation turns.
9. Verify enabled integrations execute only through approved tool orchestration and fail safely when unconfigured.
10. Verify `/health`, `/ready`, `/metrics`, frontend production build, database migrations, backups, and HTTPS deployment checks.
11. Run the complete CI suite and require every job to pass.
12. Record representative end-to-end results in the final release notes.

## Release rule

The application is release-complete only when the above runtime acceptance checks have been executed successfully against the current `main` commit. CI success alone is not sufficient evidence of external-provider runtime behavior.
