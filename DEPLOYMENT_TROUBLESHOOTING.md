# Deployment Troubleshooting Guide

This guide covers common issues when deploying to Render.com (backend) and Vercel (frontend).

## Table of Contents

1. [Backend Issues (Render.com)](#backend-issues-rendercom)
2. [Frontend Issues (Vercel)](#frontend-issues-vercel)
3. [Integration Issues](#integration-issues)
4. [Database/Storage Issues](#databasestorage-issues)
5. [Performance Issues](#performance-issues)

## Backend Issues (Render.com)

### Service Won't Start

**Symptoms**: Service shows "Live" but requests fail, or service status is "Failed"

**Solutions**:
1. **Check Build Logs**:
   - Go to service → Logs tab
   - Look for errors during build phase
   - Common issues: missing dependencies, Python version mismatch

2. **Verify Requirements**:
   ```bash
   # Test locally
   cd backend
   pip install -r requirements.txt
   ```

3. **Check Start Command**:
   - Verify start command in Render matches your app structure
   - Should be: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Ensure `app.main:app` matches your actual module path

4. **Check Python Version**:
   - Create `runtime.txt` in backend directory with Python version
   - Example: `python-3.9.18`

### Worker Not Processing Tasks

**Symptoms**: Tasks queued but not executing, worker logs show errors

**Solutions**:
1. **Verify Redis Connection**:
   - Check worker logs for Redis connection errors
   - Ensure `REDIS_URL` uses internal Redis URL (for services in same region)
   - Format: `redis://red-xxxxx:6379`

2. **Check Task Registration**:
   ```bash
   # In worker logs, you should see:
   # [INFO/MainProcess] celery@hostname ready.
   ```

3. **Verify Environment Variables**:
   - Worker must have same environment variables as web service
   - Specifically: `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`

4. **Check Task Import Path**:
   - Ensure Celery can import tasks: `celery -A app.workers.celery_app worker`
   - Verify `app.workers.celery_app` module exists and is correct

### Health Check Failing

**Symptoms**: Service shows unhealthy status

**Solutions**:
1. **Verify Health Endpoint**:
   - Check `/health` endpoint returns 200 OK
   - Should return: `{"status": "healthy"}`

2. **Check Health Check Path**:
   - In Render service settings, health check path should be `/health`
   - Ensure no trailing slash

3. **Check Application Startup**:
   - Review logs for startup errors
   - Ensure app can bind to `0.0.0.0:$PORT`

### Cold Starts (Free Tier)

**Symptoms**: First request after inactivity takes 10-30 seconds

**Solutions**:
1. **Expected Behavior**: Free tier services sleep after 15 minutes of inactivity
2. **Keep-Alive**: Use a service like UptimeRobot to ping health endpoint every 10 minutes
3. **Upgrade**: Move to paid plan for always-on services

## Frontend Issues (Vercel)

### Build Fails

**Symptoms**: Deployment shows "Build Failed" status

**Solutions**:
1. **Check Build Logs**:
   - Vercel dashboard → Deployment → View build logs
   - Look for TypeScript errors, missing dependencies, etc.

2. **Common Issues**:
   - Missing `NEXT_PUBLIC_*` environment variables
   - TypeScript type errors
   - Missing dependencies in `package.json`
   - Build timeout (increase in settings)

3. **Test Build Locally**:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

### Environment Variables Not Working

**Symptoms**: API calls fail, Supabase errors, wrong API URLs

**Solutions**:
1. **Check Prefix**: Variables must start with `NEXT_PUBLIC_`
2. **Redeploy**: Environment variables only apply to new deployments
3. **Verify Values**: Check in Vercel dashboard → Settings → Environment Variables
4. **Check Environment**: Ensure variables set for correct environment (Production/Preview)

### API Calls Fail

**Symptoms**: Network errors, CORS errors, 404s

**Solutions**:
1. **Verify Backend URL**:
   - Check `NEXT_PUBLIC_API_BASE_URL` is correct
   - Should be: `https://your-backend.onrender.com` (no trailing slash)

2. **Check CORS**:
   - Verify backend `BACKEND_CORS_ORIGINS` includes your Vercel URL
   - Format: `https://your-app.vercel.app` (no trailing slash)
   - Redeploy backend after changing CORS

3. **Check Network Tab**:
   - Browser DevTools → Network tab
   - Look for CORS errors, 404s, or connection refused
   - Verify requests go to correct backend URL

### Authentication Issues

**Symptoms**: Login fails, auth tokens not stored, redirects don't work

**Solutions**:
1. **Verify Supabase Variables**:
   - Check `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - Ensure they match your Supabase project

2. **Check Supabase Auth Settings**:
   - Supabase dashboard → Authentication → URL Configuration
   - Add redirect URLs:
     - `https://your-app.vercel.app/**`
     - `https://your-app-*.vercel.app/**` (for preview deployments)

3. **Check Browser Console**:
   - Look for Supabase client initialization errors
   - Check for CORS errors in network tab

## Integration Issues

### CORS Errors

**Symptoms**: Browser console shows CORS policy errors

**Solutions**:
1. **Backend CORS Configuration**:
   ```python
   # In backend/app/core/config.py
   BACKEND_CORS_ORIGINS=https://your-app.vercel.app,https://your-app-preview.vercel.app
   ```
   - No trailing slashes
   - Comma-separated for multiple origins
   - Include preview deployment URLs if needed

2. **Verify Origin**:
   - Check exact origin in error message
   - Ensure it matches exactly (including protocol, no trailing slash)

3. **Redeploy Backend**:
   - After changing CORS, redeploy backend service

### Backend Not Receiving Requests

**Symptoms**: Frontend shows network errors, backend logs show no requests

**Solutions**:
1. **Check Backend URL**:
   - Verify `NEXT_PUBLIC_API_BASE_URL` is correct
   - Test backend directly: `curl https://your-backend.onrender.com/health`

2. **Check Backend Status**:
   - Render dashboard → Service status should be "Live"
   - Check health endpoint is responding

3. **Check Firewall/Network**:
   - Render services should be publicly accessible
   - Check if backend service is sleeping (free tier)

### File Upload Failures

**Symptoms**: File uploads fail, files not appearing in storage

**Solutions**:
1. **Check File Size**:
   - Default limit is 5MB
   - Check `MAX_UPLOAD_SIZE` in backend config

2. **Check Supabase Storage**:
   - Verify storage bucket exists: `bill-uploads`
   - Check storage policies allow uploads
   - Verify service role key has storage access

3. **Check Backend Logs**:
   - Render dashboard → Web service → Logs
   - Look for storage upload errors

## Database/Storage Issues

### Database Connection Errors

**Symptoms**: Backend logs show database connection errors

**Solutions**:
1. **Verify Supabase Credentials**:
   - Check `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
   - Ensure they match Supabase dashboard values

2. **Check Supabase Status**:
   - Verify Supabase project is active
   - Check for service outages

3. **Check Row Level Security**:
   - Ensure RLS policies allow service role operations
   - Service role key bypasses RLS, but verify policies for anon key

### Storage Upload Errors

**Symptoms**: Files not uploading, storage errors in logs

**Solutions**:
1. **Verify Storage Bucket**:
   - Supabase dashboard → Storage
   - Ensure `bill-uploads` bucket exists
   - Check bucket is public or policies allow uploads

2. **Check Storage Policies**:
   - Supabase dashboard → Storage → Policies
   - Ensure policies allow uploads for authenticated users

3. **Verify Service Role Key**:
   - Storage uploads use service role key
   - Ensure `SUPABASE_SERVICE_ROLE_KEY` is correct

## Performance Issues

### Slow API Responses

**Symptoms**: API calls take long time, timeouts

**Solutions**:
1. **Check Backend Logs**:
   - Look for slow queries or processing
   - Check for errors or retries

2. **Check Render Plan**:
   - Free tier has limited resources
   - Consider upgrading for better performance

3. **Optimize Database Queries**:
   - Add indexes for frequently queried columns
   - Review query performance in Supabase dashboard

4. **Check Cold Starts**:
   - Free tier services sleep after inactivity
   - First request after sleep takes 10-30 seconds

### Frontend Slow to Load

**Symptoms**: Pages take long time to load

**Solutions**:
1. **Check Bundle Size**:
   - Vercel dashboard → Analytics
   - Review bundle sizes
   - Use `@next/bundle-analyzer` to identify large dependencies

2. **Optimize Images**:
   - Use Next.js Image component
   - Optimize image formats (WebP, AVIF)

3. **Check API Response Times**:
   - Monitor backend response times
   - Optimize slow endpoints

## Quick Debugging Checklist

### Backend Issues
- [ ] Service status is "Live" in Render
- [ ] Health endpoint (`/health`) returns 200
- [ ] Build logs show no errors
- [ ] Environment variables are set correctly
- [ ] Redis connection is working (for worker)
- [ ] Worker is running and processing tasks
- [ ] Logs show no critical errors

### Frontend Issues
- [ ] Build completes successfully
- [ ] Environment variables are set (with `NEXT_PUBLIC_` prefix)
- [ ] Backend URL is correct
- [ ] Supabase credentials are correct
- [ ] No console errors in browser
- [ ] Network requests are going to correct URLs
- [ ] CORS is configured correctly

### Integration Issues
- [ ] Backend CORS includes frontend URL
- [ ] Backend is accessible (test with curl)
- [ ] Environment variables match between services
- [ ] Authentication is working
- [ ] API calls are successful

## Getting Help

1. **Check Logs First**: Most issues are visible in logs
2. **Render Logs**: Dashboard → Service → Logs tab
3. **Vercel Logs**: Dashboard → Deployment → View logs
4. **Browser Console**: Check for client-side errors
5. **Network Tab**: Check for failed requests and errors

## Common Error Messages

### "Connection refused"
- Backend service is down or sleeping (free tier)
- Backend URL is incorrect
- Port configuration issue

### "CORS policy blocked"
- Backend CORS doesn't include frontend URL
- Backend CORS configuration has trailing slash
- Need to redeploy backend after CORS changes

### "Unauthorized" or 401 errors
- Missing or invalid auth token
- Supabase JWT secret mismatch
- Token expired (check refresh logic)

### "Internal Server Error" or 500 errors
- Check backend logs for detailed error
- Usually indicates code error or missing environment variable
- Check database connection

### "Task not registered" (Celery)
- Task import path is incorrect
- Worker can't import task module
- Check `celery_app.include` configuration

