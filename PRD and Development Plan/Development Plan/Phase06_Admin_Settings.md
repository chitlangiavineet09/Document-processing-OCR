# Phase 6 – Admin & Settings Tabs

## Objectives
- Provide admin-only Settings area with four tabs: User Management, External API Configuration, LLM Prompt Configuration, and Global Job List.
- Enforce role-based access control (RBAC) so only admins see the Settings link and can perform privileged actions.
- Persist configuration changes securely and propagate them to backend services/workers.

## Scope & Deliverables
1. **RBAC foundation**
   - Extend auth middleware to load user role from `User` + `Role` tables.
   - Frontend context/hook exposing role; hide Settings nav item for non-admins.
   - Backend route protection decorator verifying role.

2. **Settings shell UI**
   - Next.js route `/settings` with Tailwind CSS tab components.
   - Lazy load tab contents to keep initial bundle small.

3. **Tab 1 – User Management**
   - Table of users: name, email, role, status (active/soft-deleted), created date.
   - Actions: Add user (modal form), Edit (inline or modal), Delete (soft delete toggle).
   - Backend endpoints:
     - GET `/admin/users`
     - POST `/admin/users`
     - PATCH `/admin/users/{id}`
     - DELETE `/admin/users/{id}` (sets soft delete flag).
   - Send invitation email placeholder or show generated password (future).

4. **Tab 2 – External API Configuration**
   - Form fields for OMS API base URLs, tokens, headers, other external service settings.
   - Data stored in `settings` table with grouping (`category='external_api'`).
   - Values encrypted at rest; decrypt on read for admins only.
   - Provide “Test connection” button calling backend proxy to validate credentials.

5. **Tab 3 – LLM Prompt & Model Config**
   - Editable text areas for classification prompt, OCR prompt, fuzzy match prompt, plus dropdown for model selection per prompt.
   - Backend stores versioned entries to allow rollbacks; workers subscribe to changes via cache invalidation or simple timestamp check.

6. **Tab 4 – Global Job List**
   - Similar UI to user job history but shows all jobs across users with columns: Job ID, User, Status, Created, Completed, Errors.
   - Filters for status/user; ability for admin to retry job (enqueue Celery task) or mark as resolved.
   - Backend GET `/admin/jobs` and POST `/admin/jobs/{id}/retry`.

## Acceptance Criteria
- Non-admin users denied access (403) to settings endpoints and UI.
- Admin can CRUD users and roles; changes reflected immediately.
- API configs saved securely and used by Phase 5 services without restarting app (pull from DB/cache).
- Prompt/model updates propagate to background workers (poll or webhook).
- Global job list accurately mirrors JobThread table and allows retry.

## Risks & Mitigations
- **Secret leakage**: ensure masking in UI (show only last 4 chars) and audit logging for reads.
- **Concurrent edits**: include `updated_at` and optimistic locking to avoid overwrites.
- **Worker config drift**: implement simple version check endpoint workers can query before each job.

## Dependencies
- Builds on existing auth + JobThread data.
- Supplies configuration consumed by Phases 2 & 5.

