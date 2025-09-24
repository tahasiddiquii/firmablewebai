"""
Unit tests for the database client module
"""

import pytest
import asyncio
import json
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock, create_autospec
import asyncpg
import numpy as np

from app.db.postgres_client import PostgresClient


class TestPostgresClient:
    """Test the PostgresClient class"""
    
    @pytest.fixture
    def db_client_no_url(self, monkeypatch):
        """Create database client without URL"""
        monkeypatch.delenv("POSTGRES_URL", raising=False)
        return PostgresClient()
    
    @pytest.fixture
    def db_client_with_url(self, monkeypatch):
        """Create database client with URL"""
        monkeypatch.setenv("POSTGRES_URL", "postgresql://test:test@localhost:5432/test")
        return PostgresClient()
    
    @pytest.fixture
    def mock_connection_pool(self):
        """Create mock connection pool"""
        mock_pool = Mock()
        mock_conn = Mock()
        
        # Create async context manager for pool.acquire()
        mock_acquire_cm = AsyncMock()
        mock_acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_cm.__aexit__ = AsyncMock()
        mock_pool.acquire.return_value = mock_acquire_cm
        
        mock_conn.execute = AsyncMock()
        mock_conn.fetchrow = AsyncMock()
        mock_conn.fetch = AsyncMock()
        return mock_pool, mock_conn
    
    def test_initialization_without_url(self, db_client_no_url):
        """Test database client initialization without URL"""
        assert db_client_no_url.connection_pool is None
        assert db_client_no_url.postgres_url is None
    
    def test_initialization_with_url(self, db_client_with_url):
        """Test database client initialization with URL"""
        assert db_client_with_url.connection_pool is None
        assert db_client_with_url.postgres_url == "postgresql://test:test@localhost:5432/test"
    
    @pytest.mark.asyncio
    async def test_initialize_no_url(self, db_client_no_url):
        """Test initialization without database URL"""
        await db_client_no_url.initialize()
        assert db_client_no_url.connection_pool is None
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, db_client_with_url):
        """Test successful database initialization"""
        with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            await db_client_with_url.initialize()
            
            assert db_client_with_url.connection_pool == mock_pool
            mock_create_pool.assert_called_once_with(
                db_client_with_url.postgres_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
    
    @pytest.mark.asyncio
    @patch('asyncpg.create_pool')
    async def test_initialize_failure(self, mock_create_pool, db_client_with_url):
        """Test database initialization failure"""
        mock_create_pool.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception, match="Connection failed"):
            await db_client_with_url.initialize()
    
    @pytest.mark.asyncio
    async def test_close_with_pool(self, db_client_with_url, mock_connection_pool):
        """Test closing database connection"""
        mock_pool, _ = mock_connection_pool
        mock_pool.close = AsyncMock()
        db_client_with_url.connection_pool = mock_pool
        
        await db_client_with_url.close()
        mock_pool.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_without_pool(self, db_client_no_url):
        """Test closing without connection pool"""
        await db_client_no_url.close()  # Should not raise
    
    @pytest.mark.asyncio
    async def test_setup_schema(self, db_client_with_url, mock_connection_pool):
        """Test database schema setup"""
        mock_pool, mock_conn = mock_connection_pool
        db_client_with_url.connection_pool = mock_pool
        
        await db_client_with_url.setup_schema()
        
        # Check that extension and tables were created
        calls = mock_conn.execute.call_args_list
        assert len(calls) == 3  # Extension + 2 tables
        
        # Check pgvector extension
        assert "CREATE EXTENSION IF NOT EXISTS vector" in str(calls[0])
        
        # Check websites table
        assert "CREATE TABLE IF NOT EXISTS websites" in str(calls[1])
        
        # Check website_chunks table
        assert "CREATE TABLE IF NOT EXISTS website_chunks" in str(calls[2])
    
    @pytest.mark.asyncio
    async def test_get_or_create_website_existing(self, db_client_with_url, mock_connection_pool):
        """Test getting existing website"""
        mock_pool, mock_conn = mock_connection_pool
        db_client_with_url.connection_pool = mock_pool
        
        # Mock existing website
        mock_conn.fetchrow.return_value = {'id': 123}
        
        website_id = await db_client_with_url.get_or_create_website("https://example.com")
        
        assert website_id == 123
        mock_conn.fetchrow.assert_called_once()
        mock_conn.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_or_create_website_new(self, db_client_with_url, mock_connection_pool):
        """Test creating new website"""
        mock_pool, mock_conn = mock_connection_pool
        db_client_with_url.connection_pool = mock_pool
        
        # Mock no existing website, then return new ID
        mock_conn.fetchrow.side_effect = [None, {'id': 456}]
        
        website_id = await db_client_with_url.get_or_create_website("https://example.com")
        
        assert website_id == 456
        assert mock_conn.fetchrow.call_count == 2
    
    @pytest.mark.asyncio
    async def test_save_insights(self, db_client_with_url, mock_connection_pool):
        """Test saving insights"""
        mock_pool, mock_conn = mock_connection_pool
        db_client_with_url.connection_pool = mock_pool
        
        insights = {
            "industry": "Technology",
            "company_size": "Large",
            "products": ["Product A", "Product B"]
        }
        
        await db_client_with_url.save_insights(1, insights)
        
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "UPDATE websites SET insights" in call_args[0]
        assert json.dumps(insights) == call_args[1]
        assert call_args[2] == 1  # website_id
    
    @pytest.mark.asyncio
    async def test_save_chunks(self, db_client_with_url, mock_connection_pool):
        """Test saving chunks with embeddings"""
        mock_pool, mock_conn = mock_connection_pool
        db_client_with_url.connection_pool = mock_pool
        
        chunks = ["Chunk 1", "Chunk 2"]
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        
        await db_client_with_url.save_chunks(1, chunks, embeddings)
        
        # Should delete existing chunks first
        delete_call = mock_conn.execute.call_args_list[0]
        assert "DELETE FROM website_chunks" in str(delete_call)
        
        # Then insert new chunks
        insert_calls = mock_conn.execute.call_args_list[1:]
        assert len(insert_calls) == 2  # Two chunks
        
        # Check first chunk insert
        first_insert = insert_calls[0][0]
        assert "INSERT INTO website_chunks" in first_insert[0]
        assert first_insert[1] == 1  # website_id
        assert first_insert[2] == "Chunk 1"
        assert first_insert[3] == "[0.1,0.2,0.3]"  # Embedding as string
    
    @pytest.mark.asyncio
    async def test_search_similar_chunks_with_results(self, db_client_with_url, mock_connection_pool):
        """Test searching for similar chunks"""
        mock_pool, mock_conn = mock_connection_pool
        db_client_with_url.connection_pool = mock_pool
        
        # Mock chunk count and search results
        mock_conn.fetchrow.return_value = {'count': 5}
        mock_conn.fetch.return_value = [
            {'chunk_text': 'Similar chunk 1', 'distance': 0.1},
            {'chunk_text': 'Similar chunk 2', 'distance': 0.2},
            {'chunk_text': 'Similar chunk 3', 'distance': 0.3}
        ]
        
        query_embedding = [0.1, 0.2, 0.3]
        results = await db_client_with_url.search_similar_chunks(query_embedding, 1, limit=3)
        
        assert len(results) == 3
        assert results[0] == 'Similar chunk 1'
        assert results[1] == 'Similar chunk 2'
        assert results[2] == 'Similar chunk 3'
        
        # Check the query
        search_call = mock_conn.fetch.call_args[0]
        assert "SELECT chunk_text, embedding <=>" in search_call[0]
        assert search_call[1] == "[0.1,0.2,0.3]"  # Embedding as string
        assert search_call[2] == 1  # website_id
        assert search_call[3] == 3  # limit
    
    @pytest.mark.asyncio
    async def test_search_similar_chunks_no_results(self, db_client_with_url, mock_connection_pool):
        """Test searching with no chunks"""
        mock_pool, mock_conn = mock_connection_pool
        db_client_with_url.connection_pool = mock_pool
        
        # Mock no chunks
        mock_conn.fetchrow.return_value = {'count': 0}
        
        query_embedding = [0.1, 0.2, 0.3]
        results = await db_client_with_url.search_similar_chunks(query_embedding, 1)
        
        assert results == []
        mock_conn.fetch.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_website_insights_exists(self, db_client_with_url, mock_connection_pool):
        """Test getting website insights"""
        mock_pool, mock_conn = mock_connection_pool
        db_client_with_url.connection_pool = mock_pool
        
        insights = {"industry": "Tech", "products": ["A", "B"]}
        mock_conn.fetchrow.return_value = {'insights': insights}
        
        result = await db_client_with_url.get_website_insights(1)
        
        assert result == insights
        mock_conn.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_website_insights_not_exists(self, db_client_with_url, mock_connection_pool):
        """Test getting insights for non-existent website"""
        mock_pool, mock_conn = mock_connection_pool
        db_client_with_url.connection_pool = mock_pool
        
        mock_conn.fetchrow.return_value = None
        
        result = await db_client_with_url.get_website_insights(999)
        
        assert result is None


class TestPostgresClientIntegration:
    """Integration tests for database client"""
    
    @pytest.mark.asyncio
    @pytest.mark.requires_db
    async def test_full_database_flow(self, monkeypatch):
        """Test full database flow (requires PostgreSQL)"""
        # This test only runs if POSTGRES_URL is set
        postgres_url = os.environ.get("POSTGRES_URL")
        if not postgres_url:
            pytest.skip("POSTGRES_URL not set")
        
        monkeypatch.setenv("POSTGRES_URL", postgres_url)
        
        client = PostgresClient()
        
        try:
            # Initialize and setup
            await client.initialize()
            await client.setup_schema()
            
            # Create website
            url = "https://test-example.com"
            website_id = await client.get_or_create_website(url)
            assert isinstance(website_id, int)
            
            # Save insights
            insights = {
                "industry": "Test Industry",
                "products": ["Product 1", "Product 2"]
            }
            await client.save_insights(website_id, insights)
            
            # Retrieve insights
            retrieved = await client.get_website_insights(website_id)
            assert retrieved == insights
            
            # Save chunks with embeddings
            chunks = ["Test chunk 1", "Test chunk 2"]
            embeddings = [[0.1] * 1536, [0.2] * 1536]  # Assuming 1536 dimensions
            await client.save_chunks(website_id, chunks, embeddings)
            
            # Search similar chunks
            query_embedding = [0.15] * 1536
            similar = await client.search_similar_chunks(query_embedding, website_id, limit=2)
            assert len(similar) <= 2
            
        finally:
            await client.close()
    
    @pytest.mark.asyncio
    async def test_connection_pool_reuse(self):
        """Test that connection pool is reused"""
        with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            client = PostgresClient()
            client.postgres_url = "postgresql://test"
            
            # Initialize twice
            await client.initialize()
            await client.initialize()  # Should not create new pool
            
            # Pool should only be created once
            mock_create_pool.assert_called_once()
            
            await client.close()
    
    @pytest.mark.asyncio
    async def test_embedding_format_conversion(self):
        """Test embedding format conversion for pgvector"""
        # Create test client and mock
        from unittest.mock import patch
        client = PostgresClient()
        client.postgres_url = "postgresql://test"
        
        mock_pool = Mock()
        mock_conn = Mock()
        
        # Create async context manager for pool.acquire()
        mock_acquire_cm = AsyncMock()
        mock_acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_cm.__aexit__ = AsyncMock()
        mock_pool.acquire.return_value = mock_acquire_cm
        
        mock_conn.execute = AsyncMock()
        client.connection_pool = mock_pool
        
        # Test with various embedding formats
        chunks = ["Chunk"]
        embeddings = [[0.123456789, -0.987654321, 1.0, 0.0]]
        
        await client.save_chunks(1, chunks, embeddings)
        
        # Check the embedding was properly formatted
        insert_call = mock_conn.execute.call_args_list[1]  # Skip delete call
        embedding_str = insert_call[0][3]
        
        assert embedding_str.startswith("[")
        assert embedding_str.endswith("]")
        assert "0.123456789" in embedding_str
        assert "-0.987654321" in embedding_str
        assert "1.0" in embedding_str
        assert "0.0" in embedding_str
