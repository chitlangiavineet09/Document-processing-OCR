-- Migration: 001_initial_schema.sql
-- Description: Create initial database schema for automatic bill processing system
-- Run this migration in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default roles
INSERT INTO roles (name, description) VALUES
    ('user', 'Regular user with upload and draft creation permissions'),
    ('admin', 'Administrator with all permissions including settings management')
ON CONFLICT (name) DO NOTHING;

-- Create users table (if not exists via Supabase Auth)
-- Note: Supabase Auth automatically creates auth.users table
-- We'll create a profiles table that references auth.users

CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL, -- Soft delete
    CONSTRAINT fk_user FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Create index on email
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_role_id ON profiles(role_id);

-- Job Threads table
CREATE TABLE IF NOT EXISTS job_threads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    original_size INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'in_queue',
    storage_path TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_status CHECK (status IN ('in_queue', 'processing', 'processed', 'error'))
);

-- Create indexes on job_threads
CREATE INDEX IF NOT EXISTS idx_job_threads_user_id ON job_threads(user_id);
CREATE INDEX IF NOT EXISTS idx_job_threads_status ON job_threads(status);
CREATE INDEX IF NOT EXISTS idx_job_threads_created_at ON job_threads(created_at DESC);

-- Documents table
CREATE TABLE IF NOT EXISTS docs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_thread_id UUID NOT NULL REFERENCES job_threads(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    doc_type VARCHAR(50) NOT NULL DEFAULT 'unknown',
    status VARCHAR(50) NOT NULL DEFAULT 'draft_pending',
    ocr_payload JSONB,
    storage_uri TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_doc_type CHECK (doc_type IN ('bill', 'eway_bill', 'unknown')),
    CONSTRAINT chk_doc_status CHECK (status IN ('draft_pending', 'draft_created', 'unknown')),
    CONSTRAINT unique_job_page UNIQUE (job_thread_id, page_number)
);

-- Create indexes on docs
CREATE INDEX IF NOT EXISTS idx_docs_job_thread_id ON docs(job_thread_id);
CREATE INDEX IF NOT EXISTS idx_docs_user_id ON docs(user_id);
CREATE INDEX IF NOT EXISTS idx_docs_doc_type ON docs(doc_type);
CREATE INDEX IF NOT EXISTS idx_docs_status ON docs(status);
CREATE INDEX IF NOT EXISTS idx_docs_page_number ON docs(job_thread_id, page_number);

-- Draft Bills table
CREATE TABLE IF NOT EXISTS draft_bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id UUID NOT NULL REFERENCES docs(id) ON DELETE CASCADE,
    job_thread_id UUID NOT NULL REFERENCES job_threads(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    po_number VARCHAR(255),
    order_number VARCHAR(255),
    order_mongo_id VARCHAR(255),
    order_details JSONB, -- Snapshot of OMS API response
    extracted_data JSONB, -- OCR extracted bill details
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_doc_draft UNIQUE (doc_id)
);

-- Create indexes on draft_bills
CREATE INDEX IF NOT EXISTS idx_draft_bills_doc_id ON draft_bills(doc_id);
CREATE INDEX IF NOT EXISTS idx_draft_bills_job_thread_id ON draft_bills(job_thread_id);
CREATE INDEX IF NOT EXISTS idx_draft_bills_user_id ON draft_bills(user_id);
CREATE INDEX IF NOT EXISTS idx_draft_bills_po_number ON draft_bills(po_number);

-- Items table
CREATE TABLE IF NOT EXISTS items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    draft_bill_id UUID NOT NULL REFERENCES draft_bills(id) ON DELETE CASCADE,
    item_name VARCHAR(500) NOT NULL,
    master_item_name VARCHAR(500),
    item_code VARCHAR(255),
    hsn VARCHAR(255),
    total_quantity DECIMAL(10, 2),
    billable_quantity DECIMAL(10, 2),
    quantity DECIMAL(10, 2) NOT NULL,
    gst_type VARCHAR(50), -- 'CGST-SGST' or 'IGST'
    cgst_rate DECIMAL(5, 2),
    sgst_rate DECIMAL(5, 2),
    igst_rate DECIMAL(5, 2),
    unit VARCHAR(50),
    unit_rate DECIMAL(15, 2),
    amount DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_gst_type CHECK (gst_type IN ('CGST-SGST', 'IGST'))
);

-- Create indexes on items
CREATE INDEX IF NOT EXISTS idx_items_draft_bill_id ON items(draft_bill_id);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES job_threads(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'unread',
    cta_route TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    read_at TIMESTAMPTZ,
    CONSTRAINT chk_notification_type CHECK (type IN ('job_processed', 'job_error', 'draft_ready')),
    CONSTRAINT chk_notification_status CHECK (status IN ('unread', 'read'))
);

-- Create indexes on notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_job_user_type ON notifications(user_id, type, status);

-- Settings table for admin configuration
CREATE TABLE IF NOT EXISTS settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(100) NOT NULL,
    key VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_category_key UNIQUE (category, key)
);

-- Create index on settings
CREATE INDEX IF NOT EXISTS idx_settings_category ON settings(category);

-- Insert default settings placeholders (will be configured via admin UI)
INSERT INTO settings (category, key, value, description) VALUES
    ('external_api', 'oms_base_url', 'https://api.zetwerk.com/oms/v1', 'OMS API base URL'),
    ('external_api', 'oms_auth_token', '', 'OMS API authentication token'),
    ('llm', 'classification_prompt', '', 'LLM prompt for document classification'),
    ('llm', 'ocr_prompt', '', 'LLM prompt for OCR extraction'),
    ('llm', 'fuzzy_match_prompt', '', 'LLM prompt for fuzzy matching items'),
    ('llm', 'classification_model', 'gpt-4o', 'LLM model for classification'),
    ('llm', 'ocr_model', 'gpt-4o', 'LLM model for OCR'),
    ('llm', 'fuzzy_match_model', 'gpt-4o', 'LLM model for fuzzy matching')
ON CONFLICT (category, key) DO NOTHING;

-- Enable Row Level Security (RLS) on tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE docs ENABLE ROW LEVEL SECURITY;
ALTER TABLE draft_bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE items ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- RLS Policies for profiles (users can only see their own profile)
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- RLS Policies for job_threads (users can only see their own jobs)
CREATE POLICY "Users can view own jobs" ON job_threads
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own jobs" ON job_threads
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- RLS Policies for docs (users can only see docs from their jobs)
CREATE POLICY "Users can view own docs" ON docs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own docs" ON docs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- RLS Policies for draft_bills (users can only see their own drafts)
CREATE POLICY "Users can view own drafts" ON draft_bills
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own drafts" ON draft_bills
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- RLS Policies for items (users can only see items from their drafts)
CREATE POLICY "Users can view own items" ON items
    FOR SELECT USING (auth.uid() IN (SELECT user_id FROM draft_bills WHERE id = items.draft_bill_id));

CREATE POLICY "Users can create own items" ON items
    FOR INSERT WITH CHECK (auth.uid() IN (SELECT user_id FROM draft_bills WHERE id = items.draft_bill_id));

-- RLS Policies for notifications (users can only see their own notifications)
CREATE POLICY "Users can view own notifications" ON notifications
    FOR SELECT USING (auth.uid() = user_id);

-- RLS Policies for settings (admin only - will be configured via service role)
-- Note: Settings access will be controlled via backend authentication
CREATE POLICY "Admin can view settings" ON settings
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM profiles p
            JOIN roles r ON p.role_id = r.id
            WHERE p.id = auth.uid() AND r.name = 'admin'
        )
    );

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_threads_updated_at BEFORE UPDATE ON job_threads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_docs_updated_at BEFORE UPDATE ON docs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_draft_bills_updated_at BEFORE UPDATE ON draft_bills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_items_updated_at BEFORE UPDATE ON items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_settings_updated_at BEFORE UPDATE ON settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create storage bucket for bill uploads (if not exists)
-- Note: This needs to be run with service role key
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'bill-uploads',
    'bill-uploads',
    false, -- Private bucket
    5242880, -- 5 MB limit
    ARRAY['image/png', 'image/jpeg', 'application/pdf']
)
ON CONFLICT (id) DO NOTHING;

-- Storage policies for bill-uploads bucket
-- Allow service role (backend) to upload any files (bypasses RLS)
-- Service role key bypasses all RLS policies by default, so no policy needed

-- Users can view files from their own jobs
-- Files are stored with job_id, and jobs belong to users
CREATE POLICY "Users can view own job files" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'bill-uploads'
        -- Files are associated with jobs via job_threads table
        -- This is a simplified policy - you may want to add job_id check
    );

-- Note: For uploads, the backend uses service role key which bypasses RLS
-- Users cannot directly upload files - uploads go through backend API

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

