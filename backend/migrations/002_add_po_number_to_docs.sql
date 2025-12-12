-- Migration: 002_add_po_number_to_docs.sql
-- Description: Add po_number column to docs table for storing extracted PO number

-- Add po_number column to docs table
ALTER TABLE docs
ADD COLUMN IF NOT EXISTS po_number VARCHAR(255);

-- Create index on po_number for faster lookups
CREATE INDEX IF NOT EXISTS idx_docs_po_number ON docs(po_number);

