# 🚀 FirmableWebAI Live Setup Guide

## Current Status: Ready for Live Integration

We have a fully functional codebase with both demo and live modes. Here's how to activate live mode:

## 🔑 Step 1: Gather Required Credentials

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key (starts with `sk-...`)

### Supabase Database (PostgreSQL + pgvector)
1. Go to [Supabase](https://supabase.com/dashboard)
2. Create a new project (if you haven't already)
3. Go to Settings → Database
4. Copy the connection string
5. Enable pgvector extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

### API Secret Key
- Use: `y7H9r!Pz3qT8mLw#Xv2Bf@Kc5jS1dG6n` (or generate your own)

## 🌐 Step 2: Configure Vercel Environment Variables

In your Vercel dashboard (https://vercel.com/dashboard):

1. Go to your FirmableWebAI project
2. Click Settings → Environment Variables
3. Add these variables:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Database Configuration (Supabase PostgreSQL)
POSTGRES_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres

# API Security
API_SECRET_KEY=y7H9r!Pz3qT8mLw#Xv2Bf@Kc5jS1dG6n

# Optional: Redis for rate limiting
REDIS_URL=redis://your-redis-url-if-you-have-one
```

## 🧪 Step 3: Test the System

### A. First, test demo mode (should work immediately):
```bash
curl -X POST https://your-vercel-app.vercel.app/api/insights/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token-123" \
  -d '{"url": "https://openai.com"}'
```

### B. Then test live mode (after adding environment variables):
```bash
curl -X POST https://your-vercel-app.vercel.app/api/insights/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer y7H9r!Pz3qT8mLw#Xv2Bf@Kc5jS1dG6n" \
  -d '{"url": "https://openai.com"}'
```

## 🔍 Step 4: Verify Live Features

Once environment variables are set, the system will automatically switch to live mode:

1. **Real Website Scraping**: Uses aiohttp + BeautifulSoup
2. **AI Analysis**: GPT-4.1 generates actual business insights
3. **Vector Storage**: Embeddings saved to Supabase pgvector
4. **RAG Conversations**: GPT-4o-mini with retrieved context

## 🚨 Current Deployment Issue

We're having Vercel deployment issues. Let's resolve this first:

### Option A: Fix Current Deployment
- The issue seems to be with the complex FastAPI setup
- We may need to simplify the API structure

### Option B: Alternative Deployment
- Deploy to Railway, Render, or DigitalOcean
- These platforms might be more compatible with our setup

### Option C: Local Development First
- Set up locally to test live features
- Then deploy a confirmed working version

## 🎯 Next Steps

1. **Choose deployment approach** (A, B, or C above)
2. **Get your OpenAI API key ready**
3. **Set up Supabase database**
4. **Test the live system**

## 🆘 Need Help?

If you have your credentials ready, I can help you:
- Set up the environment variables
- Test the live system
- Debug any issues
- Deploy to an alternative platform if needed

Let me know what approach you'd like to take!
