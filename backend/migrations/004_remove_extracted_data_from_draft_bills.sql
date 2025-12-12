-- Migration: 004_remove_extracted_data_from_draft_bills.sql
-- Description: Remove redundant extracted_data column from draft_bills table
-- Since docs.ocr_payload already stores this data and draft_bills has doc_id foreign key,
-- we can always fetch OCR data from docs table instead of duplicating it.

-- Drop the extracted_data column from draft_bills table
ALTER TABLE draft_bills
DROP COLUMN IF EXISTS extracted_data;

