#!/usr/bin/env python3
"""
Database Setup Script for FirmableWebAI
This script helps set up PostgreSQL with pgvector extension
"""

import asyncio
import os
import sys
import asyncpg

async def setup_database():
    """Set up PostgreSQL database with pgvector extension"""
    
    # Get database URL from environment
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        print("❌ POSTGRES_URL environment variable not set!")
        print("\n🔧 To set up your database:")
        print("1. Go to Railway Dashboard (https://railway.app/dashboard)")
        print("2. Select your project")
        print("3. Click on PostgreSQL service")
        print("4. Go to Variables tab")
        print("5. Copy the DATABASE_URL or CONNECTION_URL")
        print("6. Set it as POSTGRES_URL environment variable:")
        print("   export POSTGRES_URL='your_database_url_here'")
        print("\n   OR add to Railway variables:")
        print("   railway variables set POSTGRES_URL='your_database_url_here'")
        return False
    
    try:
        print(f"🔌 Connecting to database...")
        conn = await asyncpg.connect(postgres_url)
        
        print("✅ Connected to PostgreSQL!")
        
        # Enable pgvector extension
        print("🧩 Installing pgvector extension...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print("✅ pgvector extension enabled!")
        
        # Create tables
        print("📋 Creating tables...")
        
        # Create websites table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS websites (
                id SERIAL PRIMARY KEY,
                url TEXT UNIQUE NOT NULL,
                insights JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        print("✅ Created websites table")
        
        # Create website_chunks table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS website_chunks (
                id SERIAL PRIMARY KEY,
                website_id INT REFERENCES websites(id) ON DELETE CASCADE,
                chunk_text TEXT,
                embedding VECTOR(3072)
            )
        """)
        print("✅ Created website_chunks table")
        
        # Test the setup
        print("🧪 Testing database setup...")
        result = await conn.fetchval("SELECT 1")
        if result == 1:
            print("✅ Database test successful!")
        
        await conn.close()
        print("\n🎉 Database setup complete!")
        print("Your FirmableWebAI app is now ready for full RAG functionality!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure your POSTGRES_URL is correct")
        print("2. Ensure the database is running")
        print("3. Check if you have necessary permissions")
        return False

if __name__ == "__main__":
    print("🚀 FirmableWebAI Database Setup")
    print("=" * 40)
    
    success = asyncio.run(setup_database())
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Set POSTGRES_URL in Railway variables")
        print("2. Set REDIS_URL in Railway variables") 
        print("3. Deploy your app: git push origin main")
        print("4. Test full RAG functionality!")
    else:
        print("\n❌ Setup failed. Please check the instructions above.")
        sys.exit(1)
