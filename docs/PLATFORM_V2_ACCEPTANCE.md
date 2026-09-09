# Platform V2 Acceptance Checklist

Use this checklist before calling the complete upgrade production-ready.

## Customer conversation scenarios

1. Greeting and casual conversation.
2. Company-wide service/course discovery.
3. Explicit subject question.
4. Follow-up question without repeating the subject.
5. Topic switch from one subject to another.
6. Unknown subject with honest fallback.
7. Factual questions for price, duration, timings, mode, contact and admissions.
8. Multiple questions in one message.
9. Long-form details without dropping important list entries.
10. Natural-language paraphrase of knowledge-base wording.
11. Lead intent starts structured capture.
12. Invalid phone/email/name does not overwrite valid fields.
13. Previously captured lead details survive long conversations.
14. Public agent cannot use another agent's knowledge.
15. One organization cannot retrieve another organization's knowledge.

## Admin UI

1. Dashboard loads with useful operational summaries.
2. AI receptionist test workspace is responsive.
3. Agents support create/edit/publish/test flows.
4. Knowledge supports create/edit/deactivate/delete and clear status.
5. Documents surface processing and errors clearly.
6. Leads support review and status management.
7. Conversations support transcript inspection.
8. Analytics and integrations surfaces load without dead ends.
9. Mobile navigation works.
10. Loading, empty and error states are consistent.

## Release gate

- Backend tests green.
- API/tenant tests green.
- Frontend lint green.
- Frontend production build green.
- GitHub Actions green.
- No secrets or generated artifacts committed.
- PR reviewed and merged only after all checks pass.