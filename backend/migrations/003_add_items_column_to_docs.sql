-- Migration: 003_add_items_column_to_docs.sql
-- Description: Add items column to docs table for storing extracted items from OCR payload

-- Add items column to docs table (JSONB to store array of items)
ALTER TABLE docs
ADD COLUMN IF NOT EXISTS items JSONB;

-- Create index on items for faster queries (GIN index for JSONB)
CREATE INDEX IF NOT EXISTS idx_docs_items ON docs USING GIN (items);

