# AI Receptionist V3 Specification

## Goal
Make each AI receptionist a genuinely configurable, knowledge-scoped customer-facing assistant. A receptionist must use only tenant-shared knowledge plus the knowledge items explicitly assigned to that receptionist, and its answers must be grounded in those verified records.

## Required behavior

### Receptionist creation
The create receptionist workflow must provide:
- name
- public URL slug
- welcome message
- behavior/system instructions
- multi-select knowledge items/documents already available in the organization
- clear indication of shared vs receptionist-specific knowledge

The selection must be persisted on the server. Do not rely on client-only state.

### Knowledge management
Knowledge records remain organization-owned. Each record can be:
- shared: `agent_id = NULL`, available to every receptionist in the organization
- receptionist-specific: `agent_id = <owned agent id>`, available only to that receptionist

Users must be able to create/upload knowledge, assign it to a receptionist, move/reassign it, deactivate it, and see which receptionist(s) it serves. Never allow an agent from another organization to be selected.

### Retrieval contract
For an agent chat, retrieval must be scoped to:
- same `organization_id`
- active shared records (`agent_id IS NULL`)
- active records belonging to the current `agent_id`

Never include knowledge belonging exclusively to another receptionist.

### Answer contract
Prefer deterministic answers from verified knowledge for factual intents. Use the configured LLM only for synthesis where needed, passing verified knowledge context and receptionist instructions. Never allow the LLM to invent company facts, override tenant scope, choose a different agent, or replace verified database values.

Support:
- course/service listing
- fees/pricing/discounts
- duration
- timings/schedule
- mode/location/contact
- syllabus/topics/details
- multi-question requests
- follow-up questions referring to the active topic
- natural paraphrases
- unknown facts with a clear missing-information response

### Public chat
The public chat endpoint must resolve the published receptionist from the slug, then pass that exact `agent_id` and `organization_id` into chat orchestration.

## Acceptance tests
1. Create two receptionists A and B.
2. Create shared knowledge S, A-only knowledge A1, B-only knowledge B1.
3. Chat with A: S and A1 are retrievable; B1 is impossible to retrieve.
4. Chat with B: S and B1 are retrievable; A1 is impossible to retrieve.
5. Create receptionist from the UI and select multiple knowledge items; refresh the page and verify the assignments persist.
6. Reassign an item from A to B; A can no longer use it and B can.
7. Deactivate a knowledge item; it no longer contributes to answers.
8. Upload a document and assign its generated knowledge to a receptionist.
9. Test public chat and authenticated tester with the same receptionist; results remain within the same knowledge boundary.
10. Test company-wide questions, subject-specific questions, paraphrases, follow-ups, multi-part questions, and unknown facts.
11. Backend tests, frontend lint/build, integration tests, tenant isolation, and security checks must pass.
