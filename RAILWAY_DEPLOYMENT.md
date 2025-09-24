# 🚂 Railway Deployment Guide for FirmableWebAI

## ✅ Current Status: READY FOR RAILWAY DEPLOYMENT!

Your FirmableWebAI project has been optimized for Railway deployment with a unified FastAPI application structure.

## 🏗️ Project Structure Changes Made

### ✅ Removed Vercel Dependencies:
- ❌ `vercel.json` - Vercel configuration
- ❌ `DEPLOYMENT_GUIDE.md` - Vercel-specific guide
- ❌ `LIVE_SETUP_GUIDE.md` - Vercel setup instructions
- ❌ `test_deployment.py` - Vercel test script

### ✅ Added Railway Configuration:
- ✅ `main.py` - Unified FastAPI application
- ✅ `Procfile` - Railway process definition
- ✅ `railway.toml` - Railway deployment config
- ✅ `nixpacks.toml` - Build configuration
- ✅ `test_railway.py` - Railway-specific testing
- ✅ Updated `requirements.txt` - Latest stable versions

### ✅ API Restructuring:
- **Before**: Separate serverless functions (`/api/insights/`, `/api/query/`)
- **After**: Unified FastAPI app (`/api/insights`, `/api/query`)
- **Benefits**: Better for long-running processes, database connections, and Scrapy operations

## 🚂 Railway Deployment Steps

### 1. **Create Railway Account & Project**

1. Go to [Railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your `firmablewebai` repository

### 2. **Railway Will Auto-Deploy**

Railway will automatically:
- Detect Python project
- Install dependencies from `requirements.txt`
- Use `Procfile` to start the application
- Assign a public URL (e.g., `https://your-app.railway.app`)

### 3. **Configure Environment Variables**

In Railway dashboard, add these environment variables:

#### Required for Live Mode:
```bash
# OpenAI API
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Database (PostgreSQL with pgvector)
POSTGRES_URL=postgresql://user:password@host:5432/database

# API Security
API_SECRET_KEY=y7H9r!Pz3qT8mLw#Xv2Bf@Kc5jS1dG6n
```

#### Optional:
```bash
# Custom port (Railway sets this automatically)
PORT=8000

# Redis for rate limiting (if needed)
REDIS_URL=redis://your-redis-url
```

### 4. **Set Up PostgreSQL Database**

#### Option A: Railway PostgreSQL Plugin
1. In Railway dashboard, click "New Service"
2. Select "PostgreSQL"
3. Railway will create database and provide connection URL
4. Enable pgvector extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

#### Option B: External Database (Supabase)
1. Go to [Supabase](https://supabase.com)
2. Create new project
3. Go to Settings → Database
4. Copy connection string
5. Enable pgvector in SQL editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

## 🧪 Testing Your Deployment

### 1. **Test Demo Mode (Works Immediately)**
```bash
# Health check
curl https://your-app.railway.app/api/health

# Website analysis (demo)
curl -X POST https://your-app.railway.app/api/insights \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token-123" \
  -d '{"url": "https://openai.com"}'

# RAG query (demo)
curl -X POST https://your-app.railway.app/api/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token-123" \
  -d '{"url": "https://openai.com", "query": "What does this company do?"}'
```

### 2. **Test Live Mode (After Adding Environment Variables)**
```bash
# Use your actual API secret key
curl -X POST https://your-app.railway.app/api/insights \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer y7H9r!Pz3qT8mLw#Xv2Bf@Kc5jS1dG6n" \
  -d '{"url": "https://openai.com"}'
```

### 3. **Use Test Script**
```bash
# Update URL in test_railway.py then run:
python test_railway.py https://your-app.railway.app
```

## 🎯 Deployment Modes

### 🔄 Demo Mode
- **When**: No environment variables set
- **Features**: Mock responses for testing
- **Perfect for**: Initial deployment verification

### 🚀 Live Mode
- **When**: Environment variables configured
- **Features**: Real AI analysis, database storage, RAG conversations
- **Requires**: OpenAI API key + PostgreSQL database

## 🔧 Railway Advantages Over Vercel

| Feature | Vercel | Railway |
|---------|---------|---------|
| **Function Type** | Serverless (15s timeout) | Long-running servers |
| **Database Connections** | Limited connection pooling | Persistent connections |
| **Scrapy Operations** | Limited by timeout | Full async support |
| **Cold Starts** | Every request | Minimal (always warm) |
| **Memory Limits** | 1024MB max | Up to 8GB |
| **Deployment** | Complex serverless setup | Simple unified app |

## 📊 Expected Performance

- **First Request**: ~1-2 seconds (warm server)
- **Subsequent Requests**: ~200-500ms
- **Demo Mode**: Always fast (no external calls)
- **Live Mode**: 3-10 seconds (depends on website complexity)
- **Database Operations**: Fast with persistent connections

## 🛠️ Manual Steps for You

### Step 1: Create Railway Project
1. Go to [Railway.app](https://railway.app)
2. Sign up with GitHub
3. Create new project from your GitHub repo

### Step 2: Wait for Initial Deploy
- Railway will auto-deploy in ~2-3 minutes
- Check build logs for any issues

### Step 3: Test Demo Mode
- Visit your Railway URL
- Test API endpoints with demo token

### Step 4: Add Environment Variables (For Live Mode)
1. Get OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Set up PostgreSQL database (Railway plugin or Supabase)
3. Add environment variables in Railway dashboard
4. Redeploy (automatic after env var changes)

### Step 5: Test Live Mode
- Use your real API secret key
- Test with actual website analysis

## 🐛 Troubleshooting

### If Build Fails:
1. Check Railway build logs
2. Verify `requirements.txt` syntax
3. Ensure Python version compatibility

### If App Won't Start:
1. Check Railway deploy logs
2. Verify `main.py` runs locally: `python main.py`
3. Check port configuration (Railway sets PORT automatically)

### If API Returns Errors:
1. Check Railway application logs
2. Verify environment variables are set correctly
3. Test with demo token first
4. Check database connection string

### If Frontend Doesn't Load:
1. Ensure `/public/index.html` exists
2. Test API endpoints directly first
3. Check CORS headers in browser dev tools

## 🎉 Success Indicators

✅ Railway deployment shows "Active"  
✅ Health endpoint returns 200 OK  
✅ Demo endpoints return mock data  
✅ Frontend loads and shows UI  
✅ API authentication works with demo token  
✅ Live mode works with environment variables  

## 🚀 Next Steps After Deployment

1. **Custom Domain**: Add your own domain in Railway settings
2. **Monitoring**: Set up Railway metrics and alerts  
3. **Scaling**: Configure auto-scaling if needed
4. **Backups**: Set up database backups
5. **CI/CD**: Connect GitHub for automatic deployments

## 💰 Railway Pricing

- **Hobby Plan**: $5/month for personal projects
- **Pro Plan**: Usage-based pricing for production
- **Free Trial**: $5 credit to get started

Railway is generally more cost-effective than Vercel for applications like this that benefit from persistent connections and longer execution times.

---

**🎯 Ready to deploy? Just follow the manual steps above, and your FirmableWebAI will be live on Railway!**
