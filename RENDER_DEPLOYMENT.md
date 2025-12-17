# Render.com Backend Deployment Guide

This guide walks you through deploying the FastAPI backend with Celery workers on Render.com.

## Prerequisites

- GitHub repository with your code
- Render.com account (sign up at https://render.com)
- Supabase project with database and storage configured
- OpenAI API key

## Architecture Overview

You'll deploy three services on Render:
1. **Web Service** - FastAPI API server
2. **Background Worker** - Celery worker for async task processing
3. **Redis Service** - Managed Redis for Celery broker and result backend

## Step 1: Prepare Your Repository

Ensure your repository contains:
- `backend/` directory with your FastAPI application
- `backend/requirements.txt` with all Python dependencies
- `backend/render.yaml` (optional, for Infrastructure as Code)
- `backend/Procfile` (if not using render.yaml)

## Step 2: Create Redis Service

1. Go to your Render dashboard: https://dashboard.render.com
2. Click **"New +"** → **"Redis"**
3. Configure:
   - **Name**: `bill-processor-redis` (or your preferred name)
   - **Plan**: Starter (free tier) or Standard/Pro for production
   - **Region**: Choose closest to your other services
   - **Max Memory Policy**: `allkeys-lru`
4. Click **"Create Redis"**
5. **Important**: Note the **Internal Redis URL** - you'll need this for connecting other services

## Step 3: Create FastAPI Web Service

1. In Render dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure the service:
   - **Name**: `bill-processor-api` (or your preferred name)
   - **Environment**: `Python 3`
   - **Region**: Same region as Redis
   - **Branch**: `main` (or your production branch)
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`

4. **Environment Variables**: Add the following (click "Advanced" → "Add Environment Variable"):

   ```
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
   SUPABASE_JWT_SECRET=your-supabase-jwt-secret
   SUPABASE_STORAGE_BUCKET=bill-uploads
   
   # OpenAI Configuration
   OPENAI_API_KEY=sk-your-openai-api-key
   
   # Redis Configuration (use Internal Redis URL from Step 2)
   REDIS_URL=redis://red-xxxxx:6379  # Use Internal Redis URL
   CELERY_BROKER_URL=redis://red-xxxxx:6379  # Same as REDIS_URL
   CELERY_RESULT_BACKEND=redis://red-xxxxx:6379  # Same as REDIS_URL
   
   # CORS Configuration (will be updated after frontend deployment)
   BACKEND_CORS_ORIGINS=https://your-frontend.vercel.app
   
   # Application Settings
   ENVIRONMENT=production
   DEBUG=false
   ```

5. **Link Redis Service**:
   - Scroll to "Links" section
   - Select your Redis service
   - This automatically adds `REDIS_URL` environment variable

6. Click **"Create Web Service"**

## Step 4: Create Celery Background Worker

1. In Render dashboard, click **"New +"** → **"Background Worker"**
2. Configure:
   - **Name**: `bill-processor-worker`
   - **Environment**: `Python 3`
   - **Repository**: Same repository as web service
   - **Branch**: Same branch as web service
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `celery -A app.workers.celery_app worker --loglevel=info`

3. **Environment Variables**: Add the same environment variables as the web service
   - You can copy from the web service or manually add them
   - **Important**: Use the same Redis service connection

4. **Link Redis Service**: Link the same Redis service created in Step 2

5. Click **"Create Background Worker"**

## Step 5: Configure Auto-Deploy

Both services support auto-deploy from GitHub:

1. Go to each service settings
2. Ensure **"Auto-Deploy"** is enabled
3. Services will automatically redeploy on git push to the configured branch

## Step 6: Verify Deployment

1. **Check Web Service**:
   - Visit your service URL: `https://your-service.onrender.com`
   - Should see: `{"message": "Automatic Bill Processing System API", "version": "1.0.0"}`
   - Health check: `https://your-service.onrender.com/health`
   - Should return: `{"status": "healthy"}`

2. **Check Worker Logs**:
   - Go to Background Worker service
   - Click "Logs" tab
   - Should see Celery worker started successfully: `[INFO/MainProcess] Connected to redis://...`

3. **Test API Endpoint**:
   - Use your frontend or API client (Postman, curl)
   - Test authentication and file upload endpoints

## Step 7: Update Frontend Environment Variables

After backend is deployed, update your Vercel frontend environment variables:

1. Go to Vercel dashboard → Your project → Settings → Environment Variables
2. Update `NEXT_PUBLIC_API_BASE_URL` to your Render backend URL
3. Redeploy frontend if needed

4. Update backend CORS:
   - Go to Render → Web Service → Environment
   - Update `BACKEND_CORS_ORIGINS` with your Vercel frontend URL
   - Format: `https://your-app.vercel.app` (comma-separated if multiple)

## Using render.yaml (Alternative Method)

Instead of creating services manually, you can use `render.yaml` for Infrastructure as Code:

1. Ensure `backend/render.yaml` exists in your repository
2. In Render dashboard, click **"New +"** → **"Blueprint"**
3. Connect your repository
4. Render will detect `render.yaml` and create all services automatically
5. You'll still need to add environment variables manually or via Render's API

## Environment Variables Reference

### Required for Web Service & Worker

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://xxxxx.supabase.co` |
| `SUPABASE_KEY` | Supabase anon key | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `SUPABASE_JWT_SECRET` | Supabase JWT secret | `your-jwt-secret-here` |
| `SUPABASE_STORAGE_BUCKET` | Storage bucket name | `bill-uploads` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-xxxxx...` |
| `REDIS_URL` | Redis connection URL | `redis://red-xxxxx:6379` |
| `CELERY_BROKER_URL` | Celery broker URL | Same as REDIS_URL |
| `CELERY_RESULT_BACKEND` | Celery result backend | Same as REDIS_URL |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins | `https://your-app.vercel.app` |
| `ENVIRONMENT` | Environment name | `production` |

### Auto-Set by Render

| Variable | Description |
|----------|-------------|
| `PORT` | Port number (automatically set) |
| `RENDER` | Set to `"true"` when running on Render |

## Troubleshooting

### Service Won't Start

1. **Check Build Logs**: Go to service → Logs → Check build phase for errors
2. **Verify Requirements**: Ensure `requirements.txt` has all dependencies
3. **Check Start Command**: Verify the start command matches your app structure

### Worker Not Processing Tasks

1. **Check Redis Connection**: Verify `REDIS_URL` is correct in worker environment
2. **Check Worker Logs**: Look for connection errors or task execution errors
3. **Verify Task Registration**: Ensure Celery can find your task definitions

### CORS Errors

1. **Verify CORS Origins**: Check `BACKEND_CORS_ORIGINS` includes your frontend URL
2. **Check Format**: Use comma-separated values, no trailing slashes
3. **Redeploy**: After changing CORS, redeploy the web service

### Cold Starts (Free Tier)

- Render free tier services sleep after 15 minutes of inactivity
- First request after sleep takes 10-30 seconds (cold start)
- Upgrade to paid plan to avoid cold starts

### Redis Connection Issues

1. **Use Internal Redis URL**: Services in same region should use internal URL
2. **Check Service Links**: Ensure Redis service is linked to web/worker services
3. **Verify Redis URL Format**: Should be `redis://red-xxxxx:6379` (no password in URL)

### File Upload Issues

1. **Check File Size**: Verify files are under 5MB (configurable)
2. **Check Storage**: Ensure Supabase storage bucket exists and has correct policies
3. **Check Logs**: Look for storage upload errors in web service logs

## Scaling

### Manual Scaling (Paid Plans)

1. Go to service settings
2. Adjust instance count
3. Render will automatically load balance

### Worker Scaling

- Each worker instance processes tasks independently
- Scale workers based on queue depth
- Monitor task processing time in logs

## Monitoring

- **Logs**: Real-time logs available in Render dashboard
- **Metrics**: CPU, memory, and request metrics on paid plans
- **Alerts**: Set up email alerts for service downtime

## Cost Estimation

- **Free Tier**: 
  - Web Service: 750 hours/month (sleeps after inactivity)
  - Worker: 750 hours/month (sleeps after inactivity)
  - Redis: 25MB storage
- **Starter Plan** ($7/month per service):
  - Always-on services
  - 512MB RAM, 0.5 CPU
  - 100GB bandwidth
- **Standard Plan** ($25/month per service):
  - Better performance
  - 2GB RAM, 1 CPU
  - 400GB bandwidth

## Next Steps

After deployment:
1. Update frontend environment variables
2. Test all API endpoints
3. Monitor logs for errors
4. Set up production alerts
5. Consider upgrading plans for better performance

