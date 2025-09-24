"""
Integration tests for full application flow
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.scraper.runner import SimpleScraperRunner
from app.llm.llm_client import LLMClient
from app.db.postgres_client import PostgresClient
from models.pydantic_models import ScrapedContent


class TestFullIntegrationFlow:
    """Test complete application flow from scraping to RAG"""
    
    @pytest.mark.asyncio
    async def test_complete_insights_flow(self, sample_html_content):
        """Test complete flow: scrape -> analyze -> store"""
        
        # Mock scraper
        scraper = SimpleScraperRunner()
        with patch.object(scraper, '_fetch_with_retries', return_value=sample_html_content):
            scraped_content = await scraper.scrape_website("https://example.com")
        
        assert scraped_content.title == "Test Company - AI Solutions"
        assert len(scraped_content.products) > 0
        
        # Mock LLM client
        llm_client = LLMClient()
        llm_client.available = True
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "industry": "Artificial Intelligence",
            "company_size": "Medium",
            "location": "San Francisco",
            "USP": "Cutting-edge AI solutions",
            "products": scraped_content.products,
            "target_audience": "Enterprises",
            "contact_info": scraped_content.contact_info
        })
        
        llm_client.client = Mock()
        llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        insights = await llm_client.generate_insights(scraped_content)
        
        assert insights["industry"] == "Artificial Intelligence"
        assert insights["company_size"] == "Medium"
        
        # Mock database client
        db_client = PostgresClient()
        db_client.connection_pool = Mock()
        
        mock_conn = Mock()
        mock_conn.execute = AsyncMock()
        mock_conn.fetchrow = AsyncMock(side_effect=[None, {'id': 1}])  # New website
        
        # Create async context manager for pool.acquire()
        mock_acquire_cm = AsyncMock()
        mock_acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_cm.__aexit__ = AsyncMock()
        db_client.connection_pool.acquire.return_value = mock_acquire_cm
        
        # Save to database
        website_id = await db_client.get_or_create_website("https://example.com")
        await db_client.save_insights(website_id, insights)
        
        assert website_id == 1
        assert mock_conn.execute.called
        
        await scraper.close()
    
    @pytest.mark.asyncio
    async def test_complete_rag_flow(self):
        """Test complete RAG flow: embed -> store -> search -> respond"""
        
        # Setup LLM client
        llm_client = LLMClient()
        llm_client.available = True
        llm_client.client = Mock()
        
        # Mock embedding generation
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock()]
        mock_embedding_response.data[0].embedding = [0.1] * 1536
        llm_client.client.embeddings.create = AsyncMock(return_value=mock_embedding_response)
        
        # Generate chunks and embeddings
        text = "This is a long text about AI and machine learning. " * 100
        chunks = llm_client.chunk_text(text, chunk_size=500, overlap=100)
        
        embeddings = []
        for chunk in chunks:
            embedding = await llm_client.generate_embedding(chunk)
            embeddings.append(embedding)
        
        assert len(chunks) > 1
        assert len(embeddings) == len(chunks)
        
        # Mock database storage
        db_client = PostgresClient()
        db_client.connection_pool = Mock()
        
        mock_conn = Mock()
        mock_conn.execute = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={'count': len(chunks)})
        mock_conn.fetch = AsyncMock(return_value=[
            {'chunk_text': chunks[0], 'distance': 0.1},
            {'chunk_text': chunks[1], 'distance': 0.2}
        ])
        
        # Create async context manager for pool.acquire()
        mock_acquire_cm = AsyncMock()
        mock_acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_cm.__aexit__ = AsyncMock()
        db_client.connection_pool.acquire.return_value = mock_acquire_cm
        
        # Save chunks
        await db_client.save_chunks(1, chunks, embeddings)
        
        # Search for similar chunks
        query_embedding = [0.15] * 1536
        similar_chunks = await db_client.search_similar_chunks(query_embedding, 1, limit=5)
        
        assert len(similar_chunks) == 2
        
        # Generate RAG response
        mock_rag_response = Mock()
        mock_rag_response.choices = [Mock()]
        mock_rag_response.choices[0].message.content = "Based on the content, this discusses AI and ML."
        llm_client.client.chat.completions.create = AsyncMock(return_value=mock_rag_response)
        
        answer = await llm_client.generate_rag_response(
            "What is this about?",
            similar_chunks,
            []
        )
        
        assert "AI and ML" in answer
    
    @pytest.mark.asyncio
    async def test_error_recovery_flow(self):
        """Test that the system handles errors gracefully"""
        
        # Test scraper error recovery
        scraper = SimpleScraperRunner()
        with patch.object(scraper, '_fetch_with_retries', side_effect=Exception("Network error")):
            result = await scraper.scrape_website("https://error.com")
        
        assert isinstance(result, ScrapedContent)
        assert result.raw_text == ""  # Empty but valid
        
        # Test LLM error recovery
        llm_client = LLMClient()
        llm_client.available = True
        llm_client.client = Mock()
        llm_client.client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        
        insights = await llm_client.generate_insights(result)
        assert insights["industry"] == "Business Services"  # Fallback value
        
        # Test database error recovery
        db_client = PostgresClient()
        db_client.connection_pool = Mock()
        db_client.connection_pool.acquire = AsyncMock(side_effect=Exception("DB error"))
        
        with pytest.raises(Exception):
            await db_client.get_or_create_website("https://error.com")
        
        await scraper.close()


class TestAPIIntegration:
    """Test API endpoint integration"""
    
    @pytest.mark.asyncio
    async def test_insights_to_query_flow(self, monkeypatch):
        """Test flow from insights generation to query"""
        monkeypatch.setenv("API_SECRET_KEY", "test-key")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        auth = {"Authorization": "Bearer test-key"}
        
        # Mock the processing functions
        with patch('main.process_live_insights') as mock_insights, \
             patch('main.process_live_query') as mock_query:
            
            # Setup insights mock
            mock_insights.return_value = {
                "industry": "Technology",
                "company_size": "Large",
                "location": "USA",
                "USP": "Innovation",
                "products": ["Product A"],
                "target_audience": "Businesses",
                "contact_info": {},
                "mode": "live",
                "scraped_content_length": 1000,
                "chunks_created": 10,
                "database_enabled": True
            }
            
            # Generate insights
            insights_response = client.post(
                "/api/insights",
                json={"url": "https://example.com"},
                headers=auth
            )
            
            assert insights_response.status_code == 200
            insights_data = insights_response.json()
            assert insights_data["industry"] == "Technology"
            
            # Setup query mock
            mock_query.return_value = {
                "answer": "This is a technology company that creates Product A.",
                "source_chunks": ["chunk1", "chunk2"],
                "conversation_history": [
                    {"role": "user", "content": "What does this company do?"},
                    {"role": "assistant", "content": "This is a technology company that creates Product A."}
                ]
            }
            
            # Query about the website
            query_response = client.post(
                "/api/query",
                json={
                    "url": "https://example.com",
                    "query": "What does this company do?",
                    "conversation_history": []
                },
                headers=auth
            )
            
            assert query_response.status_code == 200
            query_data = query_response.json()
            assert "technology company" in query_data["answer"].lower()
            assert len(query_data["source_chunks"]) == 2
    
    @pytest.mark.asyncio
    async def test_conversation_flow(self, monkeypatch):
        """Test multi-turn conversation flow"""
        monkeypatch.setenv("API_SECRET_KEY", "test-key")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        auth = {"Authorization": "Bearer test-key"}
        
        conversation_history = []
        
        with patch('main.process_live_query') as mock_query:
            # First query
            mock_query.return_value = {
                "answer": "We offer AI solutions.",
                "source_chunks": ["AI products"],
                "conversation_history": [
                    {"role": "user", "content": "What products do you offer?"},
                    {"role": "assistant", "content": "We offer AI solutions."}
                ]
            }
            
            response1 = client.post(
                "/api/query",
                json={
                    "url": "https://example.com",
                    "query": "What products do you offer?",
                    "conversation_history": conversation_history
                },
                headers=auth
            )
            
            assert response1.status_code == 200
            data1 = response1.json()
            conversation_history = data1["conversation_history"]
            
            # Second query with history
            mock_query.return_value = {
                "answer": "Our AI solutions cost $1000/month.",
                "source_chunks": ["Pricing info"],
                "conversation_history": conversation_history + [
                    {"role": "user", "content": "How much do they cost?"},
                    {"role": "assistant", "content": "Our AI solutions cost $1000/month."}
                ]
            }
            
            response2 = client.post(
                "/api/query",
                json={
                    "url": "https://example.com",
                    "query": "How much do they cost?",
                    "conversation_history": conversation_history
                },
                headers=auth
            )
            
            assert response2.status_code == 200
            data2 = response2.json()
            assert "$1000" in data2["answer"]
            assert len(data2["conversation_history"]) == 4  # 2 exchanges


class TestPerformanceIntegration:
    """Test performance aspects of the integration"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_scraping(self):
        """Test concurrent website scraping"""
        scraper = SimpleScraperRunner()
        
        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com"
        ]
        
        with patch.object(scraper, '_fetch_with_retries', return_value="<html><title>Test</title></html>"):
            # Scrape multiple sites concurrently
            tasks = [scraper.scrape_website(url) for url in urls]
            results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, ScrapedContent)
        
        await scraper.close()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_batch_embedding_generation(self):
        """Test batch embedding generation"""
        llm_client = LLMClient()
        llm_client.available = True
        llm_client.client = Mock()
        
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1] * 1536
        llm_client.client.embeddings.create = AsyncMock(return_value=mock_response)
        
        texts = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]
        
        # Generate embeddings concurrently
        tasks = [llm_client.generate_embedding(text) for text in texts]
        embeddings = await asyncio.gather(*tasks)
        
        assert len(embeddings) == 5
        for embedding in embeddings:
            assert len(embedding) == 1536
