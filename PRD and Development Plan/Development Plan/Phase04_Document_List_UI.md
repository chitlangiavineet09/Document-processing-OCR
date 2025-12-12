# Phase 4 – Document List UI

## Objectives
- Implement Page 4 showing all documents extracted from a processed job, sorted by page order and enriched with current draft statuses.
- Provide contextual actions (“Review draft”, “Confirm draft”) based on doc type and status.
- Prepare data pipeline for bill draft flow entry points.

## Scope & Deliverables
1. **Backend endpoint**
   - GET `/jobs/{jobId}/documents` returning array sorted by `page_number`.
   - Each entry includes: `docId`, `pageNumber`, `docType`, `status` (`draft_pending`, `draft_created`, `unknown`), `documentNumber`, `actionsAllowed`, and links to rendered thumbnails if available.
   - Enforce ownership (user can only see docs from their job) except admins.
2. **Frontend page (Next.js dynamic route)**
   - Table layout with columns: Page #, Document type, Document number, Status, Action.
   - Row colors or icons to differentiate doc types (bill vs e-way vs unknown).
   - Buttons logic:
     - `Confirm draft` visible for `docType=bill` & `status=draft_pending`.
     - `Review draft` visible for `status=draft_created`.
     - Disabled state for other combinations with tooltip reason.
   - Integrate with notification modal: when user arrives via modal CTA, highlight relevant row.
3. **Empty & error states**
   - Show placeholder message if job has zero documents or all unknown.
   - Display inline alert when backend reports job still processing (should not happen unless user bypassed guard).
4. **Interaction flows**
   - Clicking `Confirm draft` navigates to `/drafts/{docId}/confirm-po`.
   - Clicking `Review draft` navigates to `/drafts/{docId}/final`.
   - Provide “Back to job history” link for quick navigation.
5. **Performance considerations**
   - Lazy-load preview thumbnails only when modal requested to keep initial payload small.
   - Use React Query caching keyed by `jobId`.

## Acceptance Criteria
- API enforces job ownership and returns sorted list.
- UI matches wireframe styling using Tailwind CSS tables/cards.
- Action buttons obey status rules and route correctly.
- Unknown doc types display status but no actions.
- Page responsive and accessible (table scrollable on small screens).

## Risks & Mitigations
- **Large page counts**: add virtualization or paging if `Doc` count > 100; start with scroll but instrument for future optimization.
- **Race conditions**: ensure backend returns latest statuses by referencing `Doc` table in real time; allow manual refresh action.
- **Security**: verify `jobId` belongs to user before returning docs to avoid ID enumeration.

## Dependencies
- Relies on Phase 2 doc data and Phase 3 navigation.
- Feeds Phase 5 draft creation flow entry.

