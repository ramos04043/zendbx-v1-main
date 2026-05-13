# 🚀 ZenDBX Render Deployment - Step by Step Guide

## ✅ Current Status
- Backend is production-ready
- PostgreSQL database created on Render (Singapore region)
- Database credentials received

## 📊 Your Database Details
- **Internal URL**: `postgresql://zendbx_user:3aV7bVfRtSzq1o6fxIpoITfLC3DgcaA6@dpg-d7lm140js32c7389kd20-a/zendbx`
- **External URL**: `postgresql://zendbx_user:3aV7bVfRtSzq1o6fxIpoITfLC3DgcaA6@dpg-d7lm140js32c7389kd20-a.singapore-postgres.render.com/zendbx`
- **Region**: Singapore
- **Use**: Internal URL (faster, free bandwidth)

---

## 🎯 STEP 1: Initialize Database Schema

You need to run the SQL schema files to set up your database tables.

### Option A: Using psql (Recommended)

1. **Install PostgreSQL client** (if not already installed):
   - Windows: Download from https://www.postgresql.org/download/windows/
   - Or use: `winget install PostgreSQL.PostgreSQL`

2. **Connect to your Render database**:
```bash
psql "postgresql://zendbx_user:3aV7bVfRtSzq1o6fxIpoITfLC3DgcaA6@dpg-d7lm140js32c7389kd20-a.singapore-postgres.render.com/zendbx"
```

3. **Run the initialization script**:
```bash
# From your project root
psql "postgresql://zendbx_user:3aV7bVfRtSzq1o6fxIpoITfLC3DgcaA6@dpg-d7lm140js32c7389kd20-a.singapore-postgres.render.com/zendbx" -f backend/database/init_main_database.sql
```

### Option B: Using Render Dashboard

1. Go to your Render dashboard
2. Click on your PostgreSQL database
3. Click "Connect" → "External Connection"
4. Use a database client like:
   - **DBeaver** (free, cross-platform)
   - **pgAdmin** (free, PostgreSQL official)
   - **TablePlus** (paid, but nice UI)

5. Copy and paste the contents of `backend/database/init_main_database.sql`
6. Execute the SQL

### Option C: Using Python Script

I can create a Python script that connects and initializes the database for you.

---

## 🎯 STEP 2: Generate SECRET_KEY

Run this command to generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Example output**: `xK9mP2nQ5rT8wY1zA4bC6dE7fG0hJ3kL5mN8pQ1rS4tU`

Copy this - you'll need it for environment variables.

---

## 🎯 STEP 3: Create Web Service on Render

1. **Go to Render Dashboard**: https://dashboard.render.com

2. **Click "New +" → "Web Service"**

3. **Connect Repository**:
   - If using GitHub: Connect your ZenDBX repository
   - If not on GitHub yet: Push your code to GitHub first

4. **Configure Service**:
   - **Name**: `zendbx-backend`
   - **Region**: `Singapore` (same as database for lower latency)
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave empty
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r backend/requirements.txt
     ```
   - **Start Command**:
     ```bash
     cd backend && uvicorn app.main:app --host 0.0.0.0 --port 10000
     ```

5. **Instance Type**: 
   - Free tier (for testing)
   - Or Starter ($7/month) for production

---

## 🎯 STEP 4: Configure Environment Variables

In your Render web service, go to **Environment** tab and add these variables:

### Required Variables

```bash
# Database (use Internal URL - faster and free)
DATABASE_URL=postgresql://zendbx_user:3aV7bVfRtSzq1o6fxIpoITfLC3DgcaA6@dpg-d7lm140js32c7389kd20-a/zendbx

# Security (use the SECRET_KEY you generated in Step 2)
SECRET_KEY=<paste-your-generated-secret-key>

# Environment
ENVIRONMENT=production
DEBUG=false

# CORS (add your frontend URL when deployed)
ALLOWED_ORIGINS=http://localhost:3000
```

### Optional Variables (Add if you're using these features)

```bash
# AI Features (if using)
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# OAuth (if using)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# WebSocket (if deploying websocket server separately)
WEBSOCKET_SERVER_URL=https://your-websocket-server.onrender.com
```

---

## 🎯 STEP 5: Deploy

1. **Click "Create Web Service"**
2. Render will start building and deploying
3. **Wait 2-5 minutes** for first deployment
4. Watch the logs for any errors

### Expected Log Output:
```
==> Building...
==> Installing dependencies from requirements.txt
==> Starting service...
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
```

---

## 🎯 STEP 6: Test Your Deployment

Once deployed, you'll get a URL like: `https://zendbx-backend.onrender.com`

### Test Health Endpoint:
```bash
curl https://zendbx-backend.onrender.com/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-04-24T..."
}
```

### Test Main Endpoint:
```bash
curl https://zendbx-backend.onrender.com/
```

**Expected Response**:
```json
{
  "message": "Welcome to ZENDBX API",
  "version": "1.0.0",
  "status": "running"
}
```

---

## 🎯 STEP 7: Update Frontend Configuration

Once backend is deployed, update your frontend to use the production API:

**File**: `frontend/.env.local`

```bash
NEXT_PUBLIC_API_URL=https://zendbx-backend.onrender.com
```

Or in your `frontend/lib/config.ts`:
```typescript
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://zendbx-backend.onrender.com';
```

---

## 🔧 Troubleshooting

### Issue: "Build failed"
**Check**: 
- Is `requirements.txt` in the `backend` folder?
- Are all dependencies listed?
- Check build logs for specific errors

**Solution**: 
```bash
# Test locally first
cd backend
pip install -r requirements.txt
```

### Issue: "Application failed to start"
**Check**:
- Environment variables set correctly?
- DATABASE_URL using Internal URL?
- SECRET_KEY generated and set?

**Solution**: Check logs in Render dashboard

### Issue: "Database connection failed"
**Check**:
- Using Internal Database URL (not External)?
- Database is in same region as web service?
- Database credentials correct?

**Solution**: 
```bash
# Test connection locally
psql "postgresql://zendbx_user:3aV7bVfRtSzq1o6fxIpoITfLC3DgcaA6@dpg-d7lm140js32c7389kd20-a/zendbx" -c "SELECT 1;"
```

### Issue: "502 Bad Gateway"
**Check**:
- Start command correct?
- Port is 10000?
- Application actually starting?

**Solution**: Check logs for startup errors

### Issue: "CORS errors from frontend"
**Check**:
- ALLOWED_ORIGINS includes your frontend URL?
- Format: `https://your-frontend.vercel.app` (no trailing slash)

**Solution**: Update ALLOWED_ORIGINS in Render environment variables

---

## 📊 Monitoring

### View Logs:
1. Go to Render dashboard
2. Click your web service
3. Click "Logs" tab
4. See real-time logs

### View Metrics:
1. Click "Metrics" tab
2. See CPU, Memory, Request count

### Set Up Alerts:
1. Click "Settings"
2. Add notification email
3. Get alerts for downtime

---

## 💰 Cost Breakdown

### Free Tier:
- ✅ Web Service: Free (spins down after 15 min inactivity)
- ✅ PostgreSQL: Free (1GB storage, 97 hours/month)
- ✅ Total: $0/month

### Starter Tier (Recommended for Production):
- 💵 Web Service: $7/month (always on, no spin down)
- 💵 PostgreSQL: $7/month (10GB storage, always on)
- 💵 Total: $14/month

### Pro Tier:
- 💵 Web Service: $25/month (more resources)
- 💵 PostgreSQL: $20/month (50GB storage)
- 💵 Total: $45/month

---

## 🎉 Success Checklist

- [ ] Database initialized with schema
- [ ] SECRET_KEY generated
- [ ] Web service created on Render
- [ ] Environment variables configured
- [ ] Service deployed successfully
- [ ] Health endpoint returns 200 OK
- [ ] Main endpoint returns welcome message
- [ ] Frontend updated with production API URL
- [ ] CORS configured correctly
- [ ] Test login/signup works

---

## 🚀 Next Steps After Deployment

1. **Deploy Frontend**: Deploy to Vercel/Netlify
2. **Update CORS**: Add frontend URL to ALLOWED_ORIGINS
3. **Custom Domain**: Add custom domain in Render settings
4. **SSL Certificate**: Automatic with Render
5. **Monitoring**: Set up error tracking (Sentry, etc.)
6. **Backups**: Enable automatic backups in Render
7. **CI/CD**: Set up auto-deploy on git push

---

## 📞 Need Help?

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

---

**Estimated Total Time**: 15-30 minutes
**Difficulty**: Easy to Medium
**Cost**: Free tier available

Good luck with your deployment! 🚀
