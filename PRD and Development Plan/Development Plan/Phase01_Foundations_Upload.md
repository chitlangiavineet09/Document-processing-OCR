# Phase 1 – Foundations & Upload Flow

## Objectives
- Stand up baseline FastAPI backend with Celery + Redis integration, Supabase database client, and `.env` driven config.
- Bootstrap Next.js 15 + Tailwind CSS frontend with shared layout (header, nav, footer), route placeholders for all pages, and typed API client.
- Deliver Page 1 upload workflow that validates files client-side and server-side, creates `JobThread` records, and enqueues OCR/classification jobs.
- Introduce notification modal shell + polling endpoint to surface basic job state transitions in later phases.

## Scope & Deliverables
1. **Repository setup**
   - Create Python virtual environment, `pyproject.toml` (FastAPI, Uvicorn, supabase, postgrest, Pydantic v2, Celery, redis, python-multipart).
   - Define `backend/app` structure: `main.py`, `api` routers, `models`, `schemas`, `services`, `workers`.
   - Configure Prisma for database migrations and schema management. Set up `prisma/schema.prisma` with initial models (`User`, `Role`, `JobThread`, `Doc`, `DraftBill`, `Item` as empty shells).
   - Seed initial tables with default admin + user roles.
   - Add environment templates (`.env.example`) for Supabase URL, Supabase Key, Redis URL, Celery broker/result, OMS auth placeholders, OpenAI key.

2. **Frontend scaffold**
   - Initialize Next.js app with TypeScript, ESLint, Prettier.
   - Install Prisma Client, Tailwind CSS, React Query/TanStack Query for data fetching, Axios, Zustand (lightweight state) if needed.
   - Set up Prisma schema at `prisma/schema.prisma` connecting to Supabase database.
   - Build layout components using Tailwind CSS:
     - `Header` with username + settings icon placeholder.
     - `SidebarNav` with entries: Job History, Created Draft Bills, Created Draft E-Way Bills.
     - `NotificationModal` skeleton hidden by default.
   - Configure Tailwind theme (colors, typography) referencing wireframes but optimized for usability.

3. **Upload page (Page 1)**
   - UI elements per PRD:
     - Drag/drop card + “Choose File” button, accepted formats label, max-size note.
     - Inline error states for invalid extension, oversize, multiple uploads.
   - Client validations before API call; show error banners using Tailwind CSS alert components.
   - Upon valid upload, call `/jobs` POST with multipart file to backend.
   - Display optimistic “Processing…” banner and disable input until response.

4. **Backend upload endpoint**
   - POST `/jobs`: form file field, optional metadata.
   - Validate MIME type (png/jpg/jpeg/pdf) and file size ≤ 5 MB.
   - Persist `JobThread` row (`status=in_queue`, `file_name`, `original_size`, `user_id`).
   - Store raw upload temporarily (local storage or S3 stub) for worker consumption.
   - Send Celery task `process_job(job_id)`; return job payload `{jobId, status}`.

5. **Notification modal groundwork**
   - Backend GET `/jobs/updates?since=timestamp` returns job summaries for authenticated user.
   - Frontend hook polls endpoint every 20 s and stores unseen updates.
   - Modal component lists job name, status badge, CTA placeholders (actions wired in later phases).

## Data & Config Notes
- Use Supabase (PostgreSQL hosted) for database. Local dev via Docker Compose includes Supabase local setup or use cloud instance.
- Redis for Celery broker/result backend (can be local Docker or cloud).
- Create seed script for default admin + user roles using Prisma Client or Supabase client.
- Define Pydantic schema for `JobThreadCreate`, `JobThreadOut`.
- Logging: configure `structlog` or standard logging with request IDs for uploads.

## Acceptance Criteria
- Repo installs cleanly with `make dev` (or `npm install`/`pip install`).
- Uploading valid file generates DB row and Celery task (visible in Redis queue).
- Invalid files return 4xx with descriptive message shown in UI.
- Header/nav render on every page; future routes accessible but show “Coming soon”.
- Notification modal can be manually triggered via state to show stub data; polling endpoint returns empty array without errors.

## Risks & Mitigations
- **Large file handling**: enforce streaming upload + size validation before reading entire file into memory.
- **Celery connection issues**: add health-check script to verify Redis availability during startup.
- **CORS/auth**: configure shared origin + placeholder JWT middleware early to avoid refactors.

## Next Phase Dependencies
- Celery worker container must use same codebase; include instructions for `celery -A app.workers worker --loglevel=info`.
- Persisted file location and metadata needed for Phase 2 OCR pipeline.

