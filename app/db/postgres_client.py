import asyncio
import os
from typing import List, Optional, Dict, Any
import asyncpg
import numpy as np

# Import models only if available (graceful fallback for build)
try:
    from models.pydantic_models import WebsiteChunk, ScrapedContent
except ImportError:
    # Define minimal types for build compatibility
    WebsiteChunk = None
    ScrapedContent = None


class PostgresClient:
    def __init__(self):
        self.connection_pool = None
        self.postgres_url = os.getenv("POSTGRES_URL")
    
    async def initialize(self):
        """Initialize connection pool"""
        if not self.connection_pool:
            self.connection_pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=1,
                max_size=10
            )
    
    async def close(self):
        """Close connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
    
    async def setup_schema(self):
        """Create tables and enable pgvector extension"""
        async with self.connection_pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # Create websites table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS websites (
                    id SERIAL PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    insights JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create website_chunks table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS website_chunks (
                    id SERIAL PRIMARY KEY,
                    website_id INT REFERENCES websites(id) ON DELETE CASCADE,
                    chunk_text TEXT,
                    embedding VECTOR(3072)
                )
            """)
    
    async def get_or_create_website(self, url: str) -> int:
        """Get or create website record and return ID"""
        async with self.connection_pool.acquire() as conn:
            # Try to get existing website
            result = await conn.fetchrow(
                "SELECT id FROM websites WHERE url = $1", url
            )
            
            if result:
                return result['id']
            
            # Create new website record
            result = await conn.fetchrow(
                "INSERT INTO websites (url) VALUES ($1) RETURNING id", url
            )
            return result['id']
    
    async def save_insights(self, website_id: int, insights: Dict[str, Any]):
        """Save insights to website record"""
        async with self.connection_pool.acquire() as conn:
            await conn.execute(
                "UPDATE websites SET insights = $1 WHERE id = $2",
                insights, website_id
            )
    
    async def save_chunks(self, website_id: int, chunks: List[str], embeddings: List[List[float]]):
        """Save website chunks with embeddings"""
        async with self.connection_pool.acquire() as conn:
            # Delete existing chunks for this website
            await conn.execute(
                "DELETE FROM website_chunks WHERE website_id = $1", website_id
            )
            
            # Insert new chunks
            for chunk_text, embedding in zip(chunks, embeddings):
                await conn.execute(
                    "INSERT INTO website_chunks (website_id, chunk_text, embedding) VALUES ($1, $2, $3)",
                    website_id, chunk_text, embedding
                )
    
    async def search_similar_chunks(self, query_embedding: List[float], website_id: int, limit: int = 5) -> List[str]:
        """Search for similar chunks using vector similarity"""
        async with self.connection_pool.acquire() as conn:
            # Convert embedding to numpy array for pgvector
            embedding_array = np.array(query_embedding, dtype=np.float32)
            
            results = await conn.fetch(
                """
                SELECT chunk_text, embedding <=> $1 as distance
                FROM website_chunks 
                WHERE website_id = $2
                ORDER BY embedding <=> $1
                LIMIT $3
                """,
                embedding_array, website_id, limit
            )
            
            return [row['chunk_text'] for row in results]
    
    async def get_website_insights(self, website_id: int) -> Optional[Dict[str, Any]]:
        """Get stored insights for a website"""
        async with self.connection_pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT insights FROM websites WHERE id = $1", website_id
            )
            return result['insights'] if result else None


# Global instance
postgres_client = PostgresClient()
