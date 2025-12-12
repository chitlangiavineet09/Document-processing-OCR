# Phase 7 – Notification Integration

## Objectives
- Deliver real-time or near real-time user notifications for job status changes (especially completion/error) via modal/toast UI.
- Bridge Celery worker events with frontend polling or push mechanisms.
- Provide consistent notification history with clear CTAs (view job, view documents, view draft).

## Scope & Deliverables
1. **Backend notification service**
   - Table `notifications`: `id`, `user_id`, `job_id`, `type` (`job_processed`, `job_error`, `draft_ready`), `title`, `message`, `status` (`unread`,`read`), `cta_route`, timestamps.
   - Celery tasks emit notifications when:
     - Job transitions to `processed`.
     - Job errors.
     - Draft creation succeeds (Phase 5).
   - Provide API endpoints:
     - GET `/notifications?status=unread` (defaults to unread).
     - POST `/notifications/{id}/read`.
     - POST `/notifications/mark-all-read`.
2. **Event propagation**
   - Option A (initial): short polling (every 15 s) from frontend using existing job updates endpoint; now returns `notifications` payload.
   - Option B (future): Server-Sent Events or WebSocket hub; design interface so upgrade is seamless.
3. **Frontend modal & toast**
   - Expand `NotificationModal` to list recent events with timestamp and CTA buttons.
   - Add lightweight toast/snackbar for immediate feedback when new notification arrives while modal closed.
   - Provide badge counter on header bell icon.
4. **User interactions**
   - Clicking CTA routes to appropriate page and marks notification as read.
   - “Clear all” button marks every notification read.
   - Persist collapsed/expanded state in local storage.
5. **Admin visibility**
   - Admins also receive notifications for retries or settings changes if needed (optional, scope to job events for now).

## Acceptance Criteria
- When a job completes, user sees toast + modal entry within polling interval (<20 s).
- Notifications contain meaningful title/message and deep link to job/doc.
- Mark-as-read updates backend and removes badge count.
- Duplicate notifications prevented (use unique constraint on job+type).

## Risks & Mitigations
- **Polling load**: implement `If-Modified-Since` or `sinceId` to fetch only new notifications.
- **Missed notifications**: store reliably in DB; user can manually refresh modal.
- **UX overload**: throttle to avoid spamming (e.g., consolidate multiple processed jobs into summary).

## Dependencies
- Requires job lifecycle events (Phase 2) and draft events (Phase 5).
- Builds upon modal shell from Phase 1.

