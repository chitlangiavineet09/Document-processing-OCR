# Deployment Checklist

Quick reference checklist for deploying to Render.com (backend) and Vercel (frontend).

## Pre-Deployment

- [ ] Code is committed and pushed to GitHub
- [ ] All tests pass locally
- [ ] Environment variables documented
- [ ] Supabase project configured
- [ ] Database migrations ready
- [ ] OpenAI API key available

## Backend Deployment (Render.com)

### Redis Service
- [ ] Redis service created on Render
- [ ] Internal Redis URL noted
- [ ] Redis plan selected (starter/standard/pro)

### Web Service
- [ ] Web service created on Render
- [ ] GitHub repository connected
- [ ] Root directory set to `backend`
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Health check path: `/health`
- [ ] Redis service linked
- [ ] Environment variables configured:
  - [ ] `SUPABASE_URL`
  - [ ] `SUPABASE_KEY`
  - [ ] `SUPABASE_SERVICE_ROLE_KEY`
  - [ ] `SUPABASE_JWT_SECRET`
  - [ ] `SUPABASE_STORAGE_BUCKET`
  - [ ] `OPENAI_API_KEY`
  - [ ] `REDIS_URL` (from linked Redis service)
  - [ ] `CELERY_BROKER_URL` (same as REDIS_URL)
  - [ ] `CELERY_RESULT_BACKEND` (same as REDIS_URL)
  - [ ] `BACKEND_CORS_ORIGINS` (placeholder, update after frontend deploy)
  - [ ] `ENVIRONMENT=production`
- [ ] Service deployed and status is "Live"
- [ ] Health endpoint tested: `curl https://your-service.onrender.com/health`

### Background Worker
- [ ] Background worker created on Render
- [ ] Same repository as web service
- [ ] Root directory set to `backend`
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `celery -A app.workers.celery_app worker --loglevel=info`
- [ ] Redis service linked
- [ ] Same environment variables as web service
- [ ] Worker deployed and logs show successful startup

### Backend Verification
- [ ] API root endpoint works: `https://your-service.onrender.com/`
- [ ] Health check returns: `{"status": "healthy"}`
- [ ] Worker logs show Celery connected to Redis
- [ ] No critical errors in logs

## Frontend Deployment (Vercel)

### Initial Setup
- [ ] Vercel account created/connected
- [ ] GitHub repository imported
- [ ] Root directory set to `frontend`
- [ ] Framework preset: Next.js (auto-detected)
- [ ] Build command: `npm run build` (default)

### Environment Variables
- [ ] `NEXT_PUBLIC_API_BASE_URL` = Backend Render URL
- [ ] `NEXT_PUBLIC_SUPABASE_URL` = Supabase project URL
- [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY` = Supabase anon key
- [ ] Variables set for Production, Preview, and Development environments

### Deployment
- [ ] Initial deployment successful
- [ ] Build completed without errors
- [ ] Frontend accessible at Vercel URL

### Frontend Verification
- [ ] Homepage loads correctly
- [ ] No console errors in browser
- [ ] Authentication works (Supabase login)
- [ ] API calls work (check network tab)
- [ ] File upload functionality works

## Integration

### CORS Configuration
- [ ] Backend `BACKEND_CORS_ORIGINS` updated with Vercel frontend URL
- [ ] No trailing slashes in CORS origins
- [ ] Backend redeployed after CORS changes
- [ ] CORS errors resolved

### API Connectivity
- [ ] Frontend can reach backend API
- [ ] API responses are successful
- [ ] Error handling works correctly
- [ ] Retry logic functions (for transient errors)

### End-to-End Testing
- [ ] User can log in
- [ ] User can upload a file
- [ ] Job processing works (check worker logs)
- [ ] User can view job status
- [ ] User can view documents
- [ ] Draft bill creation works
- [ ] All user flows tested

## Post-Deployment

### Monitoring
- [ ] Render service logs monitored
- [ ] Vercel deployment logs checked
- [ ] Error tracking configured (optional)
- [ ] Performance metrics reviewed

### Documentation
- [ ] Deployment URLs documented
- [ ] Environment variables documented
- [ ] Team members have access
- [ ] Runbooks created (if needed)

### Security
- [ ] Environment variables are secure (not in code)
- [ ] API keys rotated if exposed
- [ ] CORS properly configured
- [ ] HTTPS enabled (automatic on Vercel/Render)

### Performance
- [ ] Cold start times acceptable
- [ ] API response times acceptable
- [ ] Frontend load times acceptable
- [ ] Optimizations applied

## Troubleshooting

If issues occur:
1. Check [DEPLOYMENT_TROUBLESHOOTING.md](./DEPLOYMENT_TROUBLESHOOTING.md)
2. Review service logs (Render/Vercel)
3. Check browser console and network tab
4. Verify environment variables
5. Test endpoints individually

## Quick Reference

### Render Services
- Web Service URL: `https://your-service.onrender.com`
- Worker: Check logs in Render dashboard
- Redis: Internal URL used automatically

### Vercel
- Frontend URL: `https://your-app.vercel.app`
- Environment Variables: Settings → Environment Variables
- Logs: Dashboard → Deployment → View logs

### Common Commands
```bash
# Test backend health
curl https://your-service.onrender.com/health

# Test backend root
curl https://your-service.onrender.com/

# Check Vercel deployment
vercel ls

# View Vercel logs
vercel logs
```

