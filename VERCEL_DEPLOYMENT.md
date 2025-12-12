# Vercel Deployment Guide for Frontend

This guide will help you deploy the Next.js frontend to Vercel.

## 📋 Prerequisites

1. **GitHub Repository**: Your code must be pushed to GitHub ✅
   - Repository: `https://github.com/chitlangiavineet09/Document-processing-OCR.git`
   - Your code is already pushed and ready!

2. **Vercel Account**: Sign up at [vercel.com](https://vercel.com) (free tier available)

3. **Backend URL**: 
   - If backend is not deployed yet, you can use your local backend URL for testing
   - For production, you'll need to deploy backend to a service like Railway, Render, or Heroku
   - Recommended: Deploy backend first, then update frontend with production backend URL

---

## 🚀 Step 1: Create Vercel Account & Install CLI (Optional)

### Option A: Using Web Interface (Easiest - Recommended)

1. Go to [vercel.com](https://vercel.com)
2. Click **"Sign Up"** or **"Log In"**
3. Choose **"Continue with GitHub"** to connect your GitHub account
4. Authorize Vercel to access your repositories

### Option B: Using Vercel CLI

```bash
# Install Vercel CLI globally
npm install -g vercel

# Login to Vercel
vercel login
```

---

## 📦 Step 2: Import Project in Vercel

### Using Web Interface:

1. **Go to Vercel Dashboard**: [vercel.com/dashboard](https://vercel.com/dashboard)

2. **Click "Add New..." → "Project"**

3. **Import Git Repository**:
   - You'll see a list of your GitHub repositories
   - Find and select: **`Document-processing-OCR`** (or your repo name)
   - Click **"Import"**

4. **Configure Project**:
   - **Project Name**: `bill-processor-frontend` (or your preferred name)
   - **Root Directory**: Click "Edit" → Select `frontend` folder
     - This tells Vercel that the Next.js app is in the `frontend` subdirectory
   - **Framework Preset**: Should auto-detect as "Next.js"
   - **Build Command**: Leave as default (`npm run build`)
   - **Output Directory**: Leave as default (`.next`)
   - **Install Command**: Leave as default (`npm install`)

---

## 🔐 Step 3: Configure Environment Variables

**Important**: Add these environment variables in Vercel before deploying:

1. **In the Vercel project setup page**, scroll down to **"Environment Variables"** section

2. **Add the following variables** (one by one):

   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   ```
   - Replace with your actual Supabase project URL

   ```env
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key-here
   ```
   - Replace with your actual Supabase anon key (from Supabase dashboard → Settings → API)

   ```env
   NEXT_PUBLIC_API_BASE_URL=https://your-backend-url.com
   ```
   - **For testing**: Use your local backend with ngrok or localtunnel
   - **For production**: Use your deployed backend URL (Railway, Render, Heroku, etc.)

3. **Set Environment**: Make sure to add these for all environments:
   - ✅ Production
   - ✅ Preview
   - ✅ Development

---

## 🎯 Step 4: Deploy

1. **Click "Deploy"** button at the bottom of the page

2. **Wait for Deployment**:
   - Vercel will automatically:
     - Install dependencies (`npm install`)
     - Build your Next.js app (`npm run build`)
     - Deploy to production

3. **Deployment Complete**: 
   - You'll get a production URL like: `https://your-project.vercel.app`
   - Vercel also creates a preview URL for each branch/PR

---

## ✅ Step 5: Verify Deployment

1. **Visit your production URL**: `https://your-project.vercel.app`

2. **Test the application**:
   - Try logging in
   - Upload a document
   - Verify API calls are working

3. **Check Browser Console** for any errors:
   - Open DevTools (F12)
   - Check Console tab for errors
   - Check Network tab for failed API calls

---

## 🔄 Step 6: Automatic Deployments

Vercel automatically deploys:
- **Production**: Every push to `main` branch
- **Preview**: Every push to other branches or PRs

**You don't need to manually deploy again!**

---

## 🔧 Troubleshooting

### Issue 1: "Build Failed" or "Missing Environment Variables"

**Solution**:
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Make sure all required variables are set:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_BASE_URL`
3. Redeploy: Go to Deployments → Click "..." → "Redeploy"

### Issue 2: "API calls failing" (CORS errors or connection refused)

**Solution**:
1. Check `NEXT_PUBLIC_API_BASE_URL` is correct
2. If backend is local, you need to:
   - Use ngrok: `ngrok http 8000` → Use the https URL
   - Or deploy backend first (recommended)
3. Backend CORS must allow your Vercel domain:
   - Update `BACKEND_CORS_ORIGINS` in backend `.env` to include your Vercel URL
   - Example: `BACKEND_CORS_ORIGINS=http://localhost:3000,https://your-project.vercel.app`

### Issue 3: "Authentication not working"

**Solution**:
1. Verify Supabase environment variables are correct
2. Check Supabase Auth settings:
   - Go to Supabase Dashboard → Authentication → URL Configuration
   - Add your Vercel URL to "Site URL": `https://your-project.vercel.app`
   - Add to "Redirect URLs": `https://your-project.vercel.app/**`

### Issue 4: "Build works locally but fails on Vercel"

**Solution**:
1. Check build logs in Vercel Dashboard → Deployments → Click on failed deployment
2. Common issues:
   - Node version mismatch (Vercel uses Node 18+ by default, which should work)
   - Missing dependencies (check `package.json`)
   - TypeScript errors (fix before deploying)

---

## 🌐 Custom Domain (Optional)

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain (e.g., `app.yourdomain.com`)
3. Follow DNS configuration instructions
4. SSL certificate is automatically provisioned by Vercel

---

## 📝 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL | `https://xxxxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key (public) | `eyJhbGciOiJIUzI1NiIs...` |
| `NEXT_PUBLIC_API_BASE_URL` | Backend API URL (production) | `https://api.yourdomain.com` |

**Note**: `NEXT_PUBLIC_*` variables are exposed to the browser. Never put secrets here!

---

## 🚀 Next Steps

1. **Deploy Backend**: Consider deploying backend to:
   - Railway: [railway.app](https://railway.app)
   - Render: [render.com](https://render.com)
   - Heroku: [heroku.com](https://heroku.com)
   - Or any Python hosting service

2. **Update Backend CORS**: Add Vercel URL to backend CORS allowed origins

3. **Update Supabase Auth**: Add Vercel URL to Supabase redirect URLs

4. **Test End-to-End**: Verify all features work in production

---

## 📚 Useful Links

- [Vercel Documentation](https://vercel.com/docs)
- [Next.js Deployment Guide](https://nextjs.org/docs/deployment)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Supabase Auth Configuration](https://supabase.com/docs/guides/auth)

---

## 🎉 Success!

Once deployed, your frontend will be available at:
- **Production**: `https://your-project.vercel.app`
- **Preview URLs**: Created for each branch/PR

Happy deploying! 🚀

