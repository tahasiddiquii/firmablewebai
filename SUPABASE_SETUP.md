# 🚀 Supabase Setup for FirmableWebAI

Complete guide to set up Supabase as your PostgreSQL + pgvector database for FirmableWebAI.

## 🎯 Why Supabase?

- ✅ **Built-in pgvector support** - No manual extension installation needed
- ✅ **Generous free tier** - 500MB database, 50MB file storage
- ✅ **Real-time capabilities** - Perfect for future features
- ✅ **Easy setup** - 5-minute configuration
- ✅ **Global CDN** - Fast worldwide access

## 📋 Step-by-Step Setup

### **Step 1: Create Supabase Project**

1. Go to [supabase.com](https://supabase.com)
2. Click **"Start your project"** → **"Sign in"**
3. Sign in with GitHub (recommended)
4. Click **"New project"**
5. Fill in:
   - **Name**: `firmablewebai`
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to your users
6. Click **"Create new project"**
7. Wait 2-3 minutes for setup to complete

### **Step 2: Enable pgvector Extension**

1. In your Supabase dashboard, go to **"SQL Editor"**
2. Click **"New query"**
3. Run this SQL to enable pgvector:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
```

4. Click **"Run"** - you should see pgvector listed

### **Step 3: Create Database Schema**

1. In **SQL Editor**, create a new query and run:

```sql
-- Create websites table
CREATE TABLE IF NOT EXISTS websites (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    insights JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create website_chunks table with vector support
CREATE TABLE IF NOT EXISTS website_chunks (
    id SERIAL PRIMARY KEY,
    website_id INT REFERENCES websites(id) ON DELETE CASCADE,
    chunk_text TEXT,
    embedding VECTOR(3072)  -- OpenAI text-embedding-3-large dimensions
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_websites_url ON websites(url);
CREATE INDEX IF NOT EXISTS idx_chunks_website_id ON website_chunks(website_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON website_chunks USING ivfflat (embedding vector_cosine_ops);

-- Verify tables were created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('websites', 'website_chunks');
```

### **Step 4: Get Connection Details**

1. Go to **"Settings"** → **"Database"**
2. Copy these values:

```bash
# Connection Details
Host: db.xxx.supabase.co
Database: postgres
Port: 5432
User: postgres
Password: [your-password-from-step-1]

# Connection String (use this for POSTGRES_URL)
postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
```

### **Step 5: Configure Environment Variables**

Add these to your Railway project:

```bash
# Set Supabase PostgreSQL URL
railway variables set POSTGRES_URL="postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres"

# Optional: Set Supabase API keys for future features
railway variables set SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
railway variables set SUPABASE_ANON_KEY="your-anon-key"
```

**To get your Supabase keys:**
1. Go to **"Settings"** → **"API"**
2. Copy **Project URL** and **anon public** key

## 🧪 Test Your Setup

### **Method 1: Using the Database Setup Script**

```bash
# Set the environment variable locally for testing
export POSTGRES_URL="postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres"

# Run the setup script
python setup_database.py
```

### **Method 2: Test with Python**

Create a test file:

```python
# test_supabase.py
import asyncio
import asyncpg
import os

async def test_connection():
    postgres_url = "postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres"
    
    try:
        conn = await asyncpg.connect(postgres_url)
        print("✅ Connected to Supabase!")
        
        # Test pgvector
        result = await conn.fetchval("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        if result:
            print("✅ pgvector extension is active!")
        
        # Test tables
        tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        print(f"✅ Found tables: {[t['table_name'] for t in tables]}")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
```

## 🚀 Deploy and Test

### **Deploy to Railway**

```bash
# Deploy with Supabase configuration
git add -A
git commit -m "🗄️ Configure Supabase PostgreSQL with pgvector"
git push origin main
```

### **Test Full Functionality**

1. **Health Check:**
```bash
curl https://firmablewebai-production.up.railway.app/api/health
```

2. **Test Real Analysis:**
```bash
curl -X POST https://firmablewebai-production.up.railway.app/api/insights \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{"url": "https://stripe.com"}'
```

3. **Test RAG Query:**
```bash
curl -X POST https://firmablewebai-production.up.railway.app/api/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{"url": "https://stripe.com", "query": "What payment methods does Stripe support?"}'
```

## 📊 Monitor Your Database

### **Supabase Dashboard**

1. **Table Editor**: View your data in real-time
2. **SQL Editor**: Run custom queries
3. **Database**: Monitor performance and usage
4. **Logs**: Debug connection issues

### **Useful Queries**

```sql
-- Check stored websites
SELECT id, url, created_at FROM websites ORDER BY created_at DESC;

-- Check chunks count
SELECT website_id, COUNT(*) as chunk_count 
FROM website_chunks 
GROUP BY website_id;

-- Test vector similarity (after you have data)
SELECT chunk_text, embedding <=> '[0,0,0,...]'::vector as distance 
FROM website_chunks 
WHERE website_id = 1 
ORDER BY distance 
LIMIT 5;
```

## 🔒 Security Best Practices

### **Row Level Security (RLS)**

If you want to add user authentication later:

```sql
-- Enable RLS on tables
ALTER TABLE websites ENABLE ROW LEVEL SECURITY;
ALTER TABLE website_chunks ENABLE ROW LEVEL SECURITY;

-- Create policies (example)
CREATE POLICY "Users can view their own websites" 
ON websites FOR SELECT 
USING (auth.uid() = user_id);
```

### **API Key Management**

- ✅ Use **anon key** for public operations
- ✅ Use **service role key** for server-side operations (more permissions)
- ✅ Never expose service role key in frontend
- ✅ Store keys in environment variables

## 🎯 Next Steps

Once Supabase is configured:

1. ✅ **Database is ready** - Full pgvector support
2. ✅ **RAG system active** - Vector similarity search working
3. ✅ **Conversation memory** - Chat history persisted
4. ✅ **Production ready** - Scalable and monitored

## 🆘 Troubleshooting

### **Connection Issues**

```bash
# Test connection string format
postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres

# Common issues:
# ❌ Wrong password
# ❌ Wrong project reference
# ❌ Missing postgres:// prefix
# ❌ Special characters in password not URL encoded
```

### **pgvector Issues**

```sql
-- Check if extension is installed
SELECT * FROM pg_extension WHERE extname = 'vector';

-- If not found, install it
CREATE EXTENSION vector;
```

### **Performance Issues**

```sql
-- Create vector index for faster similarity search
CREATE INDEX ON website_chunks USING ivfflat (embedding vector_cosine_ops);
```

---

**🎉 Your FirmableWebAI will have full RAG functionality with Supabase!**
