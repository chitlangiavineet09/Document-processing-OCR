# Omni-SaaS Boilerplate Analysis

## Repository Structure Overview

**Omni-SaaS** is a monorepo AI SaaS starter template built with:
- **Frontend**: Next.js 15+ (App Router), Tailwind CSS, TypeScript
- **Backend**: FastAPI (Python), Supabase Auth
- **Architecture**: Monorepo with PNPM workspaces + Turborepo
- **Hosting**: Vercel (frontend), Railway/Fly.io (backend)

## 📁 Project Structure

```
Omni-SaaS/
├── apps/
│   ├── web/          # Main Next.js app (user dashboard)
│   ├── admin/        # Admin interface
│   ├── landing/      # Marketing website
│   └── mobile/       # Optional mobile app (Expo)
│
├── backend/
│   ├── app/
│   │   ├── api/              # Route controllers
│   │   │   └── v1/
│   │   ├── core/             # Config, auth, security, prompts
│   │   ├── services/         # Business logic
│   │   ├── models/           # Pydantic models
│   │   ├── db/               # Database connection
│   │   └── main.py           # FastAPI entry point
│   ├── requirements.txt
│   └── .env.example
│
├── packages/         # Shared packages
│   ├── ui/          # Shared UI components
│   ├── utils/       # Shared utilities
│   └── types/       # Shared TypeScript types
│
├── docker-compose.yml
├── pnpm-workspace.yaml
└── README.md
```

## ✅ Components That CAN Be Reused

### 1. **Backend Structure** ✅
- **FastAPI setup**: Already matches our requirements
  - Location: `backend/app/main.py`
  - Includes CORS middleware, basic structure
  - FastAPI + Uvicorn already configured
  
- **Project Structure**: 
  - `app/api/` - API routes structure ✅
  - `app/core/` - Config, auth, security ✅
  - `app/services/` - Business logic layer ✅
  - `app/models/` - Pydantic schemas ✅
  - `app/db/` - Database connection ✅

- **Dependencies** (from `requirements.txt`):
  - `fastapi` ✅
  - `uvicorn[standard]` ✅
  - `pydantic>=2.0` ✅
  - `python-dotenv` ✅
  - `requests` / `httpx` ✅
  - `openai` ✅ (already included!)
  - Missing: `celery`, `redis`, `supabase`, `python-multipart` (need to add)

### 2. **Frontend Structure** ✅
- **Next.js 15 setup**: Already matches our requirements
  - App Router structure (`apps/web/app/`)
  - TypeScript configured
  - Tailwind CSS (via `@tailwindcss/postcss`)
  
- **Supabase Client**: Already included!
  - `@supabase/supabase-js` in dependencies ✅
  
- **UI Components**: 
  - Uses Radix UI components (good base for custom components)
  - Tailwind CSS for styling ✅

### 3. **Authentication Setup** ⚠️ (Partial)
- **Backend Auth**: 
  - `backend/app/core/auth.py` has placeholder `verify_supabase_token()`
  - Needs to be fully implemented with actual Supabase JWT verification
  - Structure is there, logic needs completion
  
- **Frontend Auth**: 
  - Supabase client already installed
  - Need to check if auth hooks/pages exist

### 4. **Configuration Management** ✅
- **Backend Config**: 
  - `app/core/config.py` uses `pydantic-settings`
  - Environment variables management structure ✅
  - Includes `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `OPENAI_API_KEY` ✅

### 5. **Monorepo Setup** ⚠️ (Optional)
- Uses PNPM workspaces + Turborepo
- **Decision needed**: 
  - Keep monorepo structure OR
  - Simplify to single `backend/` and `frontend/` structure (recommended for our simpler project)

## ❌ Components That Need Modification/Customization

### 1. **Backend - Add Missing Features**
- ❌ **Celery + Redis**: Not present, need to add
- ❌ **Supabase Python Client**: Not in requirements, need to add
- ❌ **File Upload Support**: `python-multipart` not included
- ❌ **Database Models**: Need to create our schema (JobThread, Doc, DraftBill, Items)
- ❌ **API Routes**: Need to create:
  - `/jobs` (POST - upload, GET - list)
  - `/jobs/{id}/documents`
  - `/drafts/{docId}/confirm-po`
  - `/drafts/{docId}/confirm-items`
  - `/notifications`
  - `/admin/*` routes

### 2. **Frontend - Customize for Our App**
- ❌ **Page Structure**: Need to create pages per wireframes:
  - Page 1: Upload page
  - Page 2: Job submission confirmation
  - Page 3: Job history
  - Page 4: Document list
  - Page 5: PO confirmation
  - Page 6: Items confirmation
  - Page 7: Final draft view
  - Settings pages (admin only)
  
- ❌ **Navigation**: Need custom sidebar with:
  - Job History
  - Created Draft Bills
  - Created Draft E-Way Bills
  - Settings (admin only)

- ❌ **Components**: Need to build:
  - File upload component
  - Job status cards
  - Document table
  - Draft bill forms
  - Notification modal

### 3. **Database Schema** ❌
- Omni-SaaS doesn't include database schema
- Need to create Supabase SQL migrations for:
  - `users` (may already exist via Supabase Auth)
  - `roles`
  - `job_threads`
  - `docs`
  - `draft_bills`
  - `items`
  - `notifications`
  - `settings`

### 4. **Worker Tasks** ❌
- No Celery workers in boilerplate
- Need to create:
  - `workers/tasks.py` with `process_job()` task
  - OCR service
  - Classification service
  - Fuzzy matching service

### 5. **External API Integration** ❌
- OMS API integration (get order details)
- Settings management for API tokens

## 🔄 Components to Modify

### 1. **Authentication**
- Backend: Complete Supabase JWT verification in `auth.py`
- Frontend: Check if auth pages exist, create if not
- Add role-based access control (User/Admin)

### 2. **Configuration**
- Add environment variables:
  - `REDIS_URL`
  - `CELERY_BROKER_URL`
  - `CELERY_RESULT_BACKEND`
  - `OMS_API_URL` (optional, can be in settings table)
  - `OMS_AUTH_TOKEN`
  - `SUPABASE_STORAGE_BUCKET`

### 3. **API Routes Structure**
- Keep the `app/api/v1/` structure
- Add new endpoints:
  - `endpoints/jobs.py`
  - `endpoints/drafts.py`
  - `endpoints/notifications.py`
  - `endpoints/admin.py`

## 📋 Implementation Strategy

### Recommended Approach:

1. **Use Omni-SaaS as Base Structure** ✅
   - Clone the repository
   - Keep the monorepo structure OR simplify to `backend/` + `frontend/`
   - Preserve FastAPI structure and Next.js setup

2. **Add Missing Backend Dependencies**:
   ```python
   celery[redis]
   redis
   supabase
   python-multipart
   pdf2image  # For PDF processing
   Pillow     # For image processing
   ```

3. **Keep Frontend Dependencies**:
   - Next.js 15 ✅
   - Tailwind CSS ✅
   - Supabase client ✅
   - Add: `@tanstack/react-query` (for data fetching)
   - Add: `axios` (for API calls)
   - Add: `zustand` (optional, for state management)

4. **Database**:
   - Use Supabase Auth for users (already in Omni-SaaS)
   - Create SQL migrations for our custom tables
   - Use Supabase Storage for file uploads

5. **Simplify if Needed**:
   - If monorepo is too complex, extract `apps/web` → `frontend/`
   - Extract `backend/` as-is (already clean structure)

## 🎯 Final Recommendations

### ✅ **REUSE**:
1. Backend FastAPI structure (`backend/app/`)
2. Frontend Next.js 15 setup with Tailwind
3. Configuration management pattern
4. Supabase client setup
5. Basic CORS and middleware structure

### ⚠️ **MODIFY**:
1. Complete Supabase auth implementation
2. Add Celery + Redis setup
3. Add file upload endpoints
4. Create all custom API routes

### ❌ **BUILD FROM SCRATCH**:
1. Database migrations (Supabase SQL)
2. Worker tasks (OCR, classification)
3. All frontend pages (wireframes)
4. Job processing pipeline
5. Draft bill creation flow
6. Admin settings UI

## 📝 Next Steps

1. **Clone Omni-SaaS** to CreateDraftBill folder
2. **Review and adapt** the structure
3. **Add missing dependencies** to backend
4. **Create database schema** via Supabase migrations
5. **Start Phase 1** implementation

---

**Conclusion**: Omni-SaaS provides a solid foundation with FastAPI + Next.js 15 + Tailwind + Supabase setup. We can reuse ~40% of the structure, modify ~20% (auth, config), and build ~40% from scratch (our business logic, pages, workers).

