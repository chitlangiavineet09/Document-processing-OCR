-- Migration: 005_populate_user_profile.sql
-- Description: Populate profiles table for existing users
-- This script helps create profile entries for users who already exist in auth.users
-- Run this query in Supabase SQL editor after replacing YOUR_USER_ID and YOUR_EMAIL

-- Step 1: Get your user_id from auth.users (if you don't know it)
-- Uncomment and run this query first to find your user_id:
-- SELECT id, email FROM auth.users WHERE email = 'your-email@example.com';

-- Step 2: Insert profile with admin role
-- Replace the following values:
--   - 'YOUR_USER_ID_HERE' with your actual user_id from auth.users
--   - 'your-email@example.com' with your actual email
--   - 'Your Full Name' with your name (optional)

-- Get admin role_id
DO $$
DECLARE
    v_user_id UUID;
    v_admin_role_id UUID;
    v_user_email TEXT;
BEGIN
    -- Set your user_id here (replace with your actual user_id)
    v_user_id := 'cd41986e-0a01-48fe-97ba-6cafcb04bcdf'::UUID;
    
    -- Get your email from auth.users (or set it manually)
    SELECT email INTO v_user_email 
    FROM auth.users 
    WHERE id = v_user_id;
    
    -- Get admin role_id
    SELECT id INTO v_admin_role_id 
    FROM roles 
    WHERE name = 'admin' 
    LIMIT 1;
    
    IF v_admin_role_id IS NULL THEN
        RAISE EXCEPTION 'Admin role not found. Please ensure roles table has admin role.';
    END IF;
    
    -- Insert or update profile
    INSERT INTO profiles (id, email, full_name, role_id, created_at, updated_at)
    VALUES (
        v_user_id,
        COALESCE(v_user_email, 'your-email@example.com'),
        'Admin User',  -- Change to your name
        v_admin_role_id,
        NOW(),
        NOW()
    )
    ON CONFLICT (id) 
    DO UPDATE SET
        email = COALESCE(EXCLUDED.email, profiles.email),
        role_id = v_admin_role_id,  -- Update to admin role
        full_name = COALESCE(EXCLUDED.full_name, profiles.full_name),
        updated_at = NOW(),
        deleted_at = NULL;  -- Ensure not soft-deleted
    
    RAISE NOTICE 'Profile created/updated for user_id: %, email: %, role: admin', v_user_id, v_user_email;
END $$;

