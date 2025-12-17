# Vercel Frontend Deployment Guide

This guide walks you through deploying the Next.js frontend on Vercel.

## Prerequisites

- GitHub repository with your frontend code
- Vercel account (sign up at https://vercel.com or use GitHub)
- Render.com backend deployed and running
- Supabase project configured

## Step 1: Prepare Your Repository

Ensure your repository contains:
- `frontend/` directory with your Next.js application
- `frontend/package.json` with all dependencies
- `frontend/next.config.mjs` with optimizations
- `.gitignore` excluding `node_modules` and `.env.local`

## Step 2: Deploy to Vercel

### Option A: Deploy via Vercel Dashboard

1. Go to https://vercel.com and sign in (use GitHub for easy integration)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. Configure project:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)
   - **Install Command**: `npm install` (default)

5. **Environment Variables**: Add the following (click "Environment Variables"):

   ```
   NEXT_PUBLIC_API_BASE_URL=https://your-backend.onrender.com
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
   ```

   **Important**: 
   - These must start with `NEXT_PUBLIC_` to be exposed to the browser
   - Add them for all environments: Production, Preview, Development

6. Click **"Deploy"**

### Option B: Deploy via Vercel CLI

1. Install Vercel CLI:
   ```bash
   npm i -g vercel
   ```

2. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

3. Login to Vercel:
   ```bash
   vercel login
   ```

4. Deploy:
   ```bash
   vercel
   ```

5. Follow prompts to configure environment variables

6. For production deployment:
   ```bash
   vercel --prod
   ```

## Step 3: Configure Domain (Optional)

1. Go to your project in Vercel dashboard
2. Click **Settings** → **Domains**
3. Add your custom domain
4. Follow DNS configuration instructions

## Step 4: Update Backend CORS

After frontend is deployed, update backend CORS origins:

1. Go to Render dashboard → Your web service → Environment
2. Update `BACKEND_CORS_ORIGINS`:
   - Development: `http://localhost:3000,http://127.0.0.1:3000`
   - Production: `https://your-app.vercel.app`
   - Multiple origins: `https://app1.vercel.app,https://app2.vercel.app` (comma-separated)
3. Redeploy backend service

## Step 5: Verify Deployment

1. **Check Frontend**:
   - Visit your Vercel deployment URL
   - Should see your application homepage
   - Check browser console for errors

2. **Test Authentication**:
   - Try logging in with Supabase authentication
   - Verify auth tokens are stored correctly

3. **Test API Calls**:
   - Upload a file (tests connection to Render backend)
   - Check browser network tab for API requests
   - Verify requests go to correct backend URL

4. **Check Build Logs**:
   - Go to Vercel dashboard → Your deployment → "Deployments"
   - Click on latest deployment to see build logs
   - Ensure build completed successfully

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | FastAPI backend URL | `https://your-app.onrender.com` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | `https://xxxxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |

**Important Notes**:
- All frontend environment variables must start with `NEXT_PUBLIC_`
- These are exposed to the browser, so don't include secrets
- Update them in Vercel dashboard → Settings → Environment Variables

## Build Configuration

The `next.config.mjs` file includes optimizations:

- **Image Optimization**: AVIF and WebP format support
- **Compression**: Gzip/Brotli compression enabled
- **Security Headers**: HSTS, XSS protection, frame options
- **Caching**: Static asset caching configured

## Continuous Deployment

Vercel automatically deploys on:

- **Push to main branch**: Deploys to production
- **Push to other branches**: Creates preview deployment
- **Pull requests**: Creates preview deployment for review

## Preview Deployments

- Every branch and PR gets a preview URL
- Share preview URLs for testing before merging
- Preview deployments use same environment variables as production (unless overridden)

## Performance Optimization

### Automatic Optimizations

Vercel automatically provides:
- **Edge Network**: Global CDN for static assets
- **Serverless Functions**: API routes run as serverless functions
- **Image Optimization**: Automatic image optimization and resizing
- **Code Splitting**: Automatic code splitting for optimal bundles

### Manual Optimizations (Already Configured)

- **React Strict Mode**: Enabled for development warnings
- **Image Formats**: AVIF and WebP support
- **Security Headers**: Configured in `next.config.mjs`
- **API Retry Logic**: Implemented in `lib/api.ts`

## Troubleshooting

### Build Fails

1. **Check Build Logs**: Vercel dashboard → Deployment → Build logs
2. **Common Issues**:
   - Missing environment variables
   - TypeScript errors
   - Missing dependencies in `package.json`
   - Build timeout (increase in settings if needed)

### API Calls Fail

1. **Check Backend URL**: Verify `NEXT_PUBLIC_API_BASE_URL` is correct
2. **Check CORS**: Ensure backend CORS includes your Vercel URL
3. **Check Network Tab**: Look for CORS or network errors
4. **Check Backend Logs**: Render dashboard → Web service → Logs

### Authentication Issues

1. **Verify Supabase Variables**: Check `NEXT_PUBLIC_SUPABASE_URL` and key
2. **Check Supabase Auth Settings**: Ensure redirect URLs are configured
3. **Check Browser Console**: Look for Supabase client errors

### Environment Variables Not Working

1. **Check Prefix**: Must start with `NEXT_PUBLIC_`
2. **Redeploy**: Environment variables only apply to new deployments
3. **Check Environment**: Ensure variables are set for correct environment (Production/Preview/Development)

### Slow Performance

1. **Check Vercel Analytics**: Enable analytics to see performance metrics
2. **Optimize Images**: Use Next.js Image component
3. **Check Bundle Size**: Analyze bundle with `@next/bundle-analyzer`
4. **Check API Response Times**: Monitor Render backend performance

## Monitoring

### Vercel Analytics

1. Go to project → Analytics
2. Enable Analytics (may require plan upgrade)
3. Monitor:
   - Page views
   - Performance metrics
   - Core Web Vitals

### Error Tracking

1. Integrate error tracking (Sentry, LogRocket, etc.)
2. Monitor runtime errors
3. Set up alerts for critical errors

## Custom Domain Setup

1. Go to Settings → Domains
2. Add your domain
3. Configure DNS records:
   - **A Record**: Point to Vercel IP
   - **CNAME**: Point to Vercel domain
4. SSL certificates are automatically provisioned

## Cost

- **Hobby Plan (Free)**:
  - Unlimited deployments
  - 100GB bandwidth/month
  - Serverless function execution time included
  - Perfect for development and small projects

- **Pro Plan ($20/month)**:
   - Everything in Hobby
   - More bandwidth
   - Team collaboration
   - Advanced analytics

## Next Steps

After deployment:
1. Test all features end-to-end
2. Set up monitoring and alerts
3. Configure custom domain (optional)
4. Enable analytics
5. Set up error tracking
6. Configure preview deployments for team workflow

## Checklist

- [ ] Repository connected to Vercel
- [ ] Environment variables configured
- [ ] Initial deployment successful
- [ ] Backend CORS updated with Vercel URL
- [ ] Authentication working
- [ ] API calls to backend working
- [ ] File uploads working
- [ ] All pages loading correctly
- [ ] No console errors
- [ ] Performance acceptable
- [ ] Custom domain configured (optional)

