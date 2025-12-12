# Automatic Bill Processing System

An automatic bill processing system where users can upload PDF/image files and the system automatically creates draft bills after fetching details from uploaded documents using OCR and classification.

## 🚀 Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **Queue**: Celery + Redis
- **Storage**: Supabase Storage
- **AI**: OpenAI for OCR and classification
- **Authentication**: Supabase Auth (JWT)

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS
- **State Management**: TanStack Query (React Query), Zustand
- **HTTP Client**: Axios
- **Authentication**: Supabase Auth (Client)

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.9+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **Redis** - For Celery (can use Docker)
4. **Supabase Account** - [Get one here](https://supabase.com/)
5. **OpenAI API Key** - [Get one here](https://platform.openai.com/api-keys)

## 🛠️ Setup Instructions

### 1. Clone Repository

```bash
cd /Users/vineet/Desktop/CreateDraftBill
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env.example .env

# Edit .env with your values:
# - SUPABASE_URL and SUPABASE_KEY (from Supabase dashboard)
# - SUPABASE_JWT_SECRET (from Supabase dashboard > Settings > API)
# - OPENAI_API_KEY
# - REDIS_URL (default: redis://localhost:6379/0)
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Copy environment file
cp env.example .env.local

# Edit .env.local with your values:
# - NEXT_PUBLIC_SUPABASE_URL (from Supabase dashboard)
# - NEXT_PUBLIC_SUPABASE_ANON_KEY (from Supabase dashboard)
# - NEXT_PUBLIC_API_BASE_URL (default: http://localhost:8000)
```

### 4. Database Setup

1. **Run Migration**:
   - Go to your Supabase dashboard
   - Navigate to SQL Editor
   - Open and run: `backend/migrations/001_initial_schema.sql`
   - This will create all tables, indexes, RLS policies, and storage bucket

2. **Create Admin User**:
   - Go to Supabase Auth dashboard
   - Create a new user manually
   - Note the user ID (UUID)
   - Update the `profiles` table to set `role_id` to the admin role ID:
     ```sql
     UPDATE profiles SET role_id = (SELECT id FROM roles WHERE name = 'admin')
     WHERE id = 'your-user-id';
     ```

### 5. Start Redis

```bash
# Using Docker (recommended)
docker-compose up -d redis

# Or install locally
# macOS: brew install redis && brew services start redis
# Ubuntu: sudo apt-get install redis-server && sudo systemctl start redis
```

### 6. Run Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
CreateDraftBill/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── core/             # Config, auth, security
│   │   ├── models/           # Pydantic schemas
│   │   ├── services/         # Business logic (Supabase, Storage)
│   │   ├── workers/          # Celery tasks
│   │   └── main.py           # FastAPI app
│   ├── migrations/           # Supabase SQL migrations
│   └── requirements.txt
│
├── frontend/
│   ├── app/                  # Next.js pages (App Router)
│   ├── components/           # React components
│   ├── lib/                  # Utilities (API client, Supabase)
│   └── package.json
│
├── docker-compose.yml        # Redis container
└── README.md
```

## 🔐 Authentication

The application uses Supabase Auth for authentication:

1. **Backend**: Validates JWT tokens from Supabase
2. **Frontend**: Uses Supabase client for login/signup
3. **Protected Routes**: API endpoints require valid JWT token in `Authorization: Bearer <token>` header

## 📝 Development Phases

This project is developed in phases:

- ✅ **Phase 1**: Foundations & Upload Flow (Current)
- ⏳ **Phase 2**: Async Processing & OCR
- ⏳ **Phase 3**: Job History UI
- ⏳ **Phase 4**: Document List UI
- ⏳ **Phase 5**: Draft Bill Creation Flow
- ⏳ **Phase 6**: Admin Settings
- ⏳ **Phase 7**: Notification Integration
- ⏳ **Phase 8**: Testing & Hardening

## 🧪 Testing

```bash
# Backend tests (to be implemented)
cd backend
pytest

# Frontend tests (to be implemented)
cd frontend
npm test
```

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 Environment Variables

### Backend (.env)
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `SUPABASE_JWT_SECRET`: Your Supabase JWT secret
- `OPENAI_API_KEY`: Your OpenAI API key
- `REDIS_URL`: Redis connection URL
- `CELERY_BROKER_URL`: Celery broker URL
- `CELERY_RESULT_BACKEND`: Celery result backend URL

### Frontend (.env.local)
- `NEXT_PUBLIC_SUPABASE_URL`: Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Your Supabase anon key
- `NEXT_PUBLIC_API_BASE_URL`: Backend API URL

## 📄 License

MIT

