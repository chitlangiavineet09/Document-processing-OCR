# Phase 8 – Testing & Hardening

## Objectives
- Ensure the entire system (frontend, backend, workers) is reliable, observable, and ready for deployment.
- Cover critical paths with automated tests, load checks, and security reviews.
- Produce deployment runbooks and environment configuration guidance.

## Scope & Deliverables
1. **Automated testing**
   - Backend unit tests with Pytest for:
     - API validators (upload limits, PO confirm).
     - Celery tasks (use `celery.app.conf.task_always_eager=True`).
     - Fuzzy match parser and validation rules.
   - Integration tests hitting ephemeral Supabase (local) or test instance + Redis via Docker Compose.
   - Frontend tests with Jest + React Testing Library for Page1 upload, job history, document list, draft flow forms, notification modal.
   - End-to-end tests (Playwright or Cypress) simulating key flows (upload → notification → draft creation).
2. **Quality gates**
   - Configure GitHub Actions/CI to run lint + tests on PR.
   - Enforce Prettier/ESLint + Ruff/mypy in pipelines.
3. **Performance & reliability**
   - Load test Celery pipeline with sample PDFs to measure throughput; document recommended worker counts.
   - Add timeouts/retries for OMS API calls and LLM requests.
   - Implement request logging + tracing (OpenTelemetry optional) for critical endpoints.
4. **Security**
   - Review RBAC enforcement, JWT expiry, CSRF handling for file uploads.
   - Vault or secrets manager integration for API tokens (document instructions even if still .env in dev).
   - Add audit logging for admin actions.
5. **Deployment readiness**
   - Dockerfiles for backend, worker, and frontend.
   - Compose or Helm templates for local + staging.
   - Documentation for deploying backend to Heroku/Railway/Render and frontend to Vercel/Netlify, including environment variable matrices.
6. **Operational runbooks**
   - Incident response guide (job stuck, notification backlog, OMS outage).
   - Data retention/cleanup scripts (purge old uploads, anonymize).
   - Monitoring checklist (Redis health, worker lag, API quotas).

## Acceptance Criteria
- CI pipeline green with unit/integration/E2E suites.
- Code coverage target met (e.g., ≥70% backend, ≥60% frontend) or justified.
- Load test report demonstrates acceptable latency and throughput for expected volume.
- Security review items tracked/resolved with sign-off.
- Deployment docs allow fresh environment bootstrap without tribal knowledge.

## Risks & Mitigations
- **Flaky tests**: use seeded data, deterministic LLM mocks in test env.
- **External API dependencies**: mock OMS/LLM in tests; provide replay fixtures.
- **Operational complexity**: keep runbooks concise, integrate health endpoints for automation.

## Dependencies
- Requires functional implementation from Phases 1–7.

