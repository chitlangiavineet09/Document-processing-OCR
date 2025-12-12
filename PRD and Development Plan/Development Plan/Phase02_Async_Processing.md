# Phase 2 – Async Processing & Data Persistence

## Objectives
- Stand up the end-to-end OCR/classification pipeline executed via Celery workers.
- Persist parsed page data into `Doc` records tied to `JobThread` and maintain accurate status transitions.
- Ensure storage and retrieval of uploaded files/pages supports later review and draft creation.

## Scope & Deliverables
1. **Celery worker containerization**
   - Create dedicated worker entrypoint (e.g., `celery -A app.workers.tasks worker -Q ocr`).
   - Configure queues for OCR/classification, retry policies, exponential backoff, and visibility timeout.
2. **Job lifecycle management**
   - `process_job(job_id)` task pipeline:
     1. Update `JobThread.status` to `processing`, set `started_at`.
     2. Split uploaded document into per-page images/PDF pages saved to object storage (local/S3 stub) with deterministic URIs.
     3. For each page call LLM classification prompt (config-driven) to label as `bill`, `eway_bill`, or `unknown`.
     4. Trigger OCR prompt per classified page using stored doc-type schema reference.
     5. Persist `Doc` record per page with `status` (draft_pending/draft_created/unknown), `page_number`, `classification`, raw OCR JSON, and storage path.
     6. On success, set `JobThread.status=processed`, `completed_at`.
   - Capture errors with structured logging and set `JobThread.status=error`, `error_message`, `failed_at`.
3. **Doc schema + migrations**
   - Add `Doc` model to Prisma schema with columns: `id`, `job_thread_id`, `user_id`, `page_number`, `doc_type`, `status`, `ocr_payload` (Json), `storage_uri`, `created_at`, `updated_at`.
   - Add indexes on `(job_thread_id, page_number)` for ordered retrieval via Prisma schema.
   - Run Prisma migration: `npx prisma migrate dev --name add_doc_table`
   - Use Supabase client (Python) in Celery workers to persist `Doc` records (Prisma Client is TypeScript-only, so Python workers use Supabase client directly).
4. **Storage service**
   - Abstraction providing `store_page(job_id, page_no, bytes) -> uri` and `fetch_page(uri)`.
   - Local dev implementation writes to `storage/jobs/{jobId}/page-{n}.png`.
   - Include clean-up task for orphaned blobs on job deletion.
5. **Monitoring & observability**
   - Celery task logging with job ID, page, elapsed times.
   - Prometheus-friendly metrics or basic stats (processed pages, failures) for future dashboards.

## Data & Config Notes
- Settings table must already hold prompt/model IDs; worker reads via `SettingsService` with caching.
- Ensure Redis URL configurable for both broker and result backend; optionally use Flower for monitoring.
- When OCR output schema changes, version the schema reference to replay jobs safely.

## Acceptance Criteria
- Running worker consumes queued tasks, updates job statuses correctly, and writes `Doc` rows matching uploaded page count.
- Each `Doc` row contains OCR JSON and storage URI retrievable for audit.
- Failed OCR/classification surfaces descriptive error in `JobThread` and stops processing remaining pages only if failure is fatal (configurable).
- Re-running worker on same job (manual retry) handles idempotently without duplicating docs.

## Risks & Mitigations
- **LLM latency/cost**: batch prompts where possible, cache results for retried pages.
- **OCR schema drift**: use JSON schema validation before insert; store `schema_version`.
- **Concurrency**: multiple workers must not double-process; leverage DB row-level locking when updating job status.

## Dependencies / Hand-offs
- Requires upload artifacts + metadata from Phase 1.
- Produces `Doc` data consumed by Phases 3–5.

