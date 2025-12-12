# Phase 3 – Job History UI

## Objectives
- Provide users with a comprehensive job history page (Page 3) reflecting every uploaded job and its current state.
- Enable navigation into document review only when jobs are eligible.
- Surface error details inline for transparency and troubleshooting.

## Scope & Deliverables
1. **Backend endpoints**
   - GET `/jobs` with pagination (`page`, `pageSize`), filtering by authenticated user.
   - Optional query params: `status`, `dateRange`.
   - Response includes `jobId`, `uploadedFileName`, `createdAt`, `status`, `errorMessage`, `documentCount`, `processedAt`.
   - Add `canReviewDocs` boolean (true when status=`processed` and docs exist).
2. **Frontend page (Next.js route `/jobs`)**
   - Layout per wireframe: sidebar nav + main content card list.
   - Each job card shows:
     - Header: “Job ID” + timestamp.
     - Status chip (In queue, Processing, Processed, Error) with color coding.
     - “Check documents” button enabled only when `canReviewDocs`; disabled state for other statuses with tooltip.
     - Error banner for jobs with `status=error` displaying stored reason.
   - Pagination controls (Previous/Next) matching design.
3. **Data fetching & caching**
   - Use React Query to fetch list, handle loading/skeletons, refetch interval (e.g., 30 s) while page visible.
   - Maintain query state so returning users keep page index.
4. **Navigation hooks**
   - Clicking “Check documents” routes to `/jobs/{jobId}/documents`.
   - Disabled button shows tooltip explaining required status.
5. **Accessibility & responsiveness**
   - Keyboard focus states for cards and pagination controls.
   - Layout stacks vertically on mobile while preserving nav access.

## Acceptance Criteria
- API returns paginated jobs; unauthorized access blocked.
- Job history page lists jobs in reverse chronological order.
- Status chips mirror backend state transitions.
- “Check documents” button disabled for non-processed jobs and enabled otherwise.
- Error jobs display reason text (from `JobThread.error_message`).

## Risks & Mitigations
- **Large job lists**: implement server-side pagination and optional search to avoid heavy payloads.
- **Real-time status drift**: auto-refetch on interval + manual refresh button.
- **Access control**: ensure user can only see their own jobs; admin override added later (Phase 6).

## Dependencies
- Requires Phase 2 job + doc persistence.
- Provides entry point to Phase 4 document list.

