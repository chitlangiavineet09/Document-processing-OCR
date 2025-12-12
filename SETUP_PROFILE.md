# Setup Your Admin Profile

## Quick Setup SQL Query

Since your user_id is `cd41986e-0a01-48fe-97ba-6cafcb04bcdf`, run this query in Supabase SQL editor:

```sql
-- Get admin role_id and insert your profile
DO $$
DECLARE
    v_user_id UUID := 'cd41986e-0a01-48fe-97ba-6cafcb04bcdf'::UUID;
    v_admin_role_id UUID;
    v_user_email TEXT;
BEGIN
    -- Get your email from auth.users
    SELECT email INTO v_user_email 
    FROM auth.users 
    WHERE id = v_user_id;
    
    -- Get admin role_id
    SELECT id INTO v_admin_role_id 
    FROM roles 
    WHERE name = 'admin' 
    LIMIT 1;
    
    IF v_admin_role_id IS NULL THEN
        RAISE EXCEPTION 'Admin role not found';
    END IF;
    
    -- Insert or update profile with admin role
    INSERT INTO profiles (id, email, full_name, role_id, created_at, updated_at)
    VALUES (
        v_user_id,
        COALESCE(v_user_email, 'your-email@example.com'),
        'Admin User',
        v_admin_role_id,
        NOW(),
        NOW()
    )
    ON CONFLICT (id) 
    DO UPDATE SET
        email = COALESCE(EXCLUDED.email, profiles.email),
        role_id = v_admin_role_id,
        full_name = COALESCE(EXCLUDED.full_name, profiles.full_name),
        updated_at = NOW(),
        deleted_at = NULL;
    
    RAISE NOTICE 'Profile created/updated successfully!';
END $$;
```

## Alternative: Simple INSERT (if profile doesn't exist)

```sql
-- Simple version - just run this:
INSERT INTO profiles (id, email, full_name, role_id, created_at, updated_at)
SELECT 
    'cd41986e-0a01-48fe-97ba-6cafcb04bcdf'::UUID,
    (SELECT email FROM auth.users WHERE id = 'cd41986e-0a01-48fe-97ba-6cafcb04bcdf'::UUID),
    'Admin User',
    (SELECT id FROM roles WHERE name = 'admin'),
    NOW(),
    NOW()
ON CONFLICT (id) 
DO UPDATE SET
    role_id = (SELECT id FROM roles WHERE name = 'admin'),
    updated_at = NOW(),
    deleted_at = NULL;
```

## Verify

After running the query, verify your profile:

```sql
SELECT 
    p.id,
    p.email,
    p.full_name,
    r.name as role_name
FROM profiles p
LEFT JOIN roles r ON p.role_id = r.id
WHERE p.id = 'cd41986e-0a01-48fe-97ba-6cafcb04bcdf'::UUID;
```

You should see `role_name = 'admin'`.

