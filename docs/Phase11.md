# Phase 11 — Testing and quality

Phase 11 makes the existing test coverage explicit and continuously verifiable
through GitHub Actions.

## Test layers

- **Unit tests:** isolated helpers and tool contracts in `backend/tests/unit`.
- **Integration tests:** service and provider boundaries, including ChatService,
  channels, integrations, and lead workflows.
- **API tests:** public health/root contracts, authentication boundaries, and
  OpenAPI route registration.
- **Multi-tenant isolation:** repository scoping, tenant resolution, and
  organization-aware authorization contracts.
- **Regression tests:** the complete backend suite and the frontend production
  build.

The workflow runs each focused layer as a separate required job and retains the
full-suite baseline as the final regression gate. No test disables external
security checks or relies on production credentials.
