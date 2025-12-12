# Phase 5 – Draft Bill Creation Flow

## Objectives
- Implement the multi-step draft bill creation experience (Pages 5–7) for bill-type documents.
- Integrate with OMS APIs to verify PO numbers and fetch order details.
- Run LLM fuzzy matching to align bill items with order items, enforce business rules, and persist draft outputs atomically.

## Scope & Deliverables
1. **Step 1 – Confirm PO number (Page 5)**
   - UI form displays OCR-fetched PO number (read from `Doc.ocr_payload`).
   - User can edit PO; validation ensures non-empty and matches expected pattern.
   - On confirm:
     - Call backend endpoint `POST /drafts/{docId}/confirm-po`.
     - Backend hits OMS API1 to fetch order mongo ID; handle HTTP errors, empty results, auth issues.
     - Persist temporary draft session state (e.g., `draft_sessions` table or Redis) containing `docId`, `poNumber`, `orderMongoId`, timestamp, user ID.
     - Return order metadata for display (supplier, order date).

2. **Step 2 – Confirm items & quantity (Page 6)**
   - On page load, backend uses stored session data to call OMS API2 for full order details (cache for short TTL).
   - Extract order items: names, master names, codes, HSN, unit, total quantity, unassigned quantity, taxes.
   - Fetch bill items extracted via OCR (Doc table JSON).
   - Invoke LLM fuzzy match service with strict prompt (per PRD) to produce one-to-one mapping; log prompt/response for audit.
   - Validate:
     - All bill items matched or flagged as unmatched (block progression until resolved).
     - Requested quantity ≤ unassigned quantity.
     - GST type derived from order taxes (CGST-SGST vs IGST) aligns with UI columns.
   - Render editable table:
     - Columns: Item, HSN, Unit rate, Total Qty, Billable Qty, Editable Quantity, GST fields (dependent on type), Amount (computed).
     - Checkbox to include/exclude item (default matched items checked).
     - Validation messages inline; disable confirm until all errors resolved.

3. **Persist draft data**
   - On confirm, backend transaction:
     - Insert into `draft_bill` table with doc/job/user foreign keys, PO number, order number, mongo ID, full OMS order snapshot JSON, extracted OCR summary.
     - Insert rows into `draft_items` table per selected item with columns defined in PRD (master names, codes, GST rates, quantities, amounts).
     - Update `Doc.status` to `draft_created`.
   - Clear transient session state.

4. **Final Draft View (Page 7)**
   - Display saved draft header (PO, supplier, totals) and items table read-only.
   - Provide actions: download JSON/PDF (future), return to documents list, or start new upload.
   - “Created Draft Bills” nav entry lists all drafts for user with quick links to this page.

5. **Error handling & recovery**
   - If OMS API fails, show actionable error allowing user to retry or change PO.
   - If LLM matching fails or returns unmatched items, provide manual resolution workflow (e.g., highlight unresolved rows, allow user to pick PO item manually).
   - Transactions ensure no partial drafts; rollback on any failure.

## Data & Security Notes
- Store OMS API credentials in settings (Phase 6) but access via secure secrets service; never log tokens.
- Log LLM prompt metadata without sensitive PO data where possible.
- Draft tables should include `version` for future edits.

## Acceptance Criteria
- User can start from document list, confirm PO, review items, and complete draft without DB inconsistencies.
- OMS API errors surface clearly and do not leave sessions dangling.
- Draft data becomes visible in Created Draft Bills page and Document list updates status to `Draft created`.
- Amount calculation formula `(quantity * unit_rate) * (1 + GST%)` verified against sample data.

## Risks & Mitigations
- **LLM mismatch accuracy**: add confidence scoring, allow manual override mapping.
- **API latency**: introduce caching and asynchronous data fetch while showing skeletons.
- **Data integrity**: use DB constraints + transactions to ensure unique draft per doc until reset.

## Dependencies
- Requires Document list actions (Phase 4) and settings for API tokens (Phase 6 for long-term management, interim .env allowed).

