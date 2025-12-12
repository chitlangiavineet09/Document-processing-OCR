# Step-by-Step Setup Guide

Follow these steps to set up the Automatic Bill Processing System.

## Step 1: Run Supabase Migration SQL ✅

**You already have a Supabase project, so let's run the migration:**

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Click on **SQL Editor** in the left sidebar
4. Click **New Query**
5. Open the migration file: `backend/migrations/001_initial_schema.sql`
6. Copy the **entire contents** of the file
7. Paste it into the SQL Editor
8. Click **Run** (or press Cmd/Ctrl + Enter)
9. Wait for it to complete - you should see success messages for all CREATE statements

**Important:** The migration will create:
- All database tables (roles, profiles, job_threads, docs, draft_bills, items, notifications, settings)
- Indexes and constraints
- Row Level Security policies
- Storage bucket `bill-uploads`
- Storage policies

---

## Step 2: Get Supabase Credentials 🔑

You'll need these from your Supabase dashboard:

1. **Go to your Supabase project dashboard**
2. **Click on "Settings" (gear icon) → "API"**
3. **Copy these values:**
   - `Project URL` → This is your `SUPABASE_URL`
   - `anon public` key → This is your `SUPABASE_KEY` (anon key)
   - `service_role` key → We'll need this later for admin operations
4. **Go to "Settings" → "Auth" → "JWT Settings"**
   - Find **JWT Secret** → This is your `SUPABASE_JWT_SECRET`

---

## Step 3: Configure Backend Environment Variables 📝

Let's create the backend `.env` file:

1. **Navigate to backend directory:**
   ```bash
   cd /Users/vineet/Desktop/CreateDraftBill/backend
   ```

2. **Copy the example file:**
   ```bash
   cp env.example .env
   ```

3. **Open `.env` file and fill in your values:**
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_KEY` - Your Supabase anon key
   - `SUPABASE_JWT_SECRET` - Your Supabase JWT secret
   - `OPENAI_API_KEY` - Your OpenAI API key (get from https://platform.openai.com/api-keys)
   - `REDIS_URL` - Keep default: `redis://localhost:6379/0` (if using Docker)
   - `CELERY_BROKER_URL` - Keep default: `redis://localhost:6379/0`
   - `CELERY_RESULT_BACKEND` - Keep default: `redis://localhost:6379/0`
   - `OMS_API_BASE_URL` - Keep default for now
   - `OMS_AUTH_TOKEN` - Leave empty for now
   - `BACKEND_CORS_ORIGINS` - Keep default: `http://localhost:3000,http://127.0.0.1:3000`

**Example `.env` file should look like:**
```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-jwt-secret-here
SUPABASE_STORAGE_BUCKET=bill-uploads
OPENAI_API_KEY=sk-xxxxx...
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
OMS_API_BASE_URL=https://api.zetwerk.com/oms/v1
OMS_AUTH_TOKEN=
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
DEBUG=false
ENVIRONMENT=development
```

---

## Step 4: Configure Frontend Environment Variables 📝

1. **Navigate to frontend directory:**
   ```bash
   cd /Users/vineet/Desktop/CreateDraftBill/frontend
   ```

2. **Copy the example file:**
   ```bash
   cp env.example .env.local
   ```

3. **Open `.env.local` and fill in:**
   - `NEXT_PUBLIC_SUPABASE_URL` - Your Supabase project URL (same as backend)
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Your Supabase anon key (same as backend)
   - `NEXT_PUBLIC_API_BASE_URL` - Keep default: `http://localhost:8000`

**Example `.env.local` file:**
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## Step 5: Install Backend Dependencies 📦

1. **Navigate to backend:**
   ```bash
   cd /Users/vineet/Desktop/CreateDraftBill/backend
   ```

2. **Create Python virtual environment:**
   ```bash
   python3 -m venv venv
   ```

3. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```
   You should see `(venv)` in your terminal prompt.

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   This will take a few minutes to install all packages.

---

## Step 6: Install Frontend Dependencies 📦

1. **Navigate to frontend:**
   ```bash
   cd /Users/vineet/Desktop/CreateDraftBill/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```
   This will take a few minutes.

---

## Step 7: Start Redis 🟥

1. **Make sure you're in the project root:**
   ```bash
   cd /Users/vineet/Desktop/CreateDraftBill
   ```

2. **Start Redis using Docker Compose:**
   ```bash
   docker-compose up -d redis
   ```

3. **Verify Redis is running:**
   ```bash
   docker ps
   ```
   You should see a container named `bill-processor-redis` running.

---

## Step 8: Start Backend Server 🚀

1. **Navigate to backend:**
   ```bash
   cd /Users/vineet/Desktop/CreateDraftBill/backend
   ```

2. **Activate virtual environment (if not already activated):**
   ```bash
   source venv/bin/activate
   ```

3. **Start FastAPI server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   You should see:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
   INFO:     Started reloader process
   INFO:     Started server process
   ```

4. **Keep this terminal open!** The backend needs to keep running.
5. **Test the backend:**
   - Open http://localhost:8000 in your browser
   - You should see: `{"message":"Automatic Bill Processing System API","version":"1.0.0"}`
   - Check API docs: http://localhost:8000/docs

---

## Step 9: Start Celery Worker 🔄

**Open a NEW terminal window** (keep the backend server running):

1. **Navigate to backend:**
   ```bash
   cd /Users/vineet/Desktop/CreateDraftBill/backend
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Start Celery worker:**
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info
   ```

   You should see:
   ```
   celery@hostname v5.x.x (dawn-chorus)
   ...
   [config]
   ...
   [tasks]
     . process_job
   ```

4. **Keep this terminal open!** The worker needs to keep running.

---

## Step 10: Start Frontend Development Server 🎨

**Open a NEW terminal window** (keep backend and worker running):

1. **Navigate to frontend:**
   ```bash
   cd /Users/vineet/Desktop/CreateDraftBill/frontend
   ```

2. **Start Next.js dev server:**
   ```bash
   npm run dev
   ```

   You should see:
   ```
   ▲ Next.js 15.x.x
   - Local:        http://localhost:3000
   ```

3. **Open your browser:**
   - Navigate to http://localhost:3000
   - You should see the upload page!

---

## 🎉 You're All Set!

Now you should have:
- ✅ Backend running on http://localhost:8000
- ✅ Celery worker running and ready to process jobs
- ✅ Frontend running on http://localhost:3000

### Quick Test

1. **Open http://localhost:3000** in your browser
2. **Try uploading a test file** (PNG, JPG, or PDF, max 5MB)
3. You should see the upload and job creation working!

---

## Troubleshooting 🔧

### If Redis won't start:
```bash
# Check if Docker is running
docker ps

# If Redis container exists but stopped, start it
docker-compose up -d redis
```

### If backend won't start:
- Check that `.env` file exists and has all required values
- Check that virtual environment is activated: `which python` should show `venv/bin/python`
- Check for import errors: `python -c "from app.main import app"`

### If frontend won't start:
- Check that `.env.local` file exists
- Check Node.js version: `node --version` (should be 18+)
- Try deleting `node_modules` and `package-lock.json`, then `npm install` again

### If Celery worker won't start:
- Make sure Redis is running: `docker ps | grep redis`
- Check Redis connection: `redis-cli ping` (should return `PONG`)
- Make sure backend `.env` has correct `REDIS_URL`

---

## Next Steps

Once everything is running:
1. Create a user account via Supabase Auth dashboard
2. Test the file upload functionality
3. Ready for Phase 2 implementation (OCR and classification)!

