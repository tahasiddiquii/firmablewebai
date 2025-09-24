import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api.website_insights import app as insights_app
from api.website_query import app as query_app
from models.pydantic_models import ScrapedContent


class TestInsightsEndpoint:
    """Test cases for the /website/insights endpoint"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(insights_app)
        self.headers = {"Authorization": "Bearer test-token"}
    
    @patch.dict(os.environ, {"API_SECRET_KEY": "test-token"})
    @patch('app.scraper.runner.scraper_runner.scrape_website')
    @patch('app.llm.llm_client.llm_client.generate_insights')
    @patch('app.db.postgres_client.postgres_client.get_or_create_website')
    @patch('app.db.postgres_client.postgres_client.save_insights')
    @patch('app.db.postgres_client.postgres_client.save_chunks')
    @patch('app.llm.llm_client.llm_client.chunk_text')
    @patch('app.llm.llm_client.llm_client.generate_embedding')
    def test_insights_endpoint_success(self, mock_embedding, mock_chunk, mock_save_chunks, 
                                     mock_save_insights, mock_get_website, mock_insights, mock_scrape):
        """Test successful insights generation"""
        # Mock responses
        mock_scrape.return_value = ScrapedContent(
            title="Test Company",
            meta_description="Test description",
            headings=["About"],
            main_content="Test content",
            hero_section="Welcome",
            products=["Product 1"],
            contact_info={},
            raw_text="Full content"
        )
        
        mock_insights.return_value = {
            "industry": "Technology",
            "company_size": "Small",
            "location": "San Francisco",
            "USP": "Innovative solutions",
            "products": ["Product 1"],
            "target_audience": "Small businesses",
            "contact_info": {}
        }
        
        mock_get_website.return_value = 1
        mock_chunk.return_value = ["chunk1", "chunk2"]
        mock_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Make request
        response = self.client.post(
            "/website/insights",
            json={"url": "https://example.com", "questions": ["What do they do?"]},
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "industry" in data
        assert "products" in data
        assert data["industry"] == "Technology"
    
    def test_insights_endpoint_missing_auth(self):
        """Test insights endpoint without authentication"""
        response = self.client.post(
            "/website/insights",
            json={"url": "https://example.com"}
        )
        
        assert response.status_code == 401
    
    def test_insights_endpoint_invalid_auth(self):
        """Test insights endpoint with invalid authentication"""
        response = self.client.post(
            "/website/insights",
            json={"url": "https://example.com"},
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestQueryEndpoint:
    """Test cases for the /website/query endpoint"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(query_app)
        self.headers = {"Authorization": "Bearer test-token"}
    
    @patch.dict(os.environ, {"API_SECRET_KEY": "test-token"})
    @patch('app.db.postgres_client.postgres_client.get_or_create_website')
    @patch('app.db.postgres_client.postgres_client.get_website_insights')
    @patch('app.llm.llm_client.llm_client.generate_embedding')
    @patch('app.db.postgres_client.postgres_client.search_similar_chunks')
    @patch('app.llm.llm_client.llm_client.generate_rag_response')
    def test_query_endpoint_success(self, mock_rag, mock_search, mock_embedding, 
                                   mock_insights, mock_get_website):
        """Test successful query processing"""
        # Mock responses
        mock_get_website.return_value = 1
        mock_insights.return_value = {"industry": "Technology"}
        mock_embedding.return_value = [0.1, 0.2, 0.3]
        mock_search.return_value = ["chunk1", "chunk2"]
        mock_rag.return_value = "This is the answer"
        
        # Make request
        response = self.client.post(
            "/website/query",
            json={
                "url": "https://example.com",
                "query": "What services do they offer?",
                "conversation_history": []
            },
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "source_chunks" in data
        assert "conversation_history" in data
        assert data["answer"] == "This is the answer"
    
    @patch.dict(os.environ, {"API_SECRET_KEY": "test-token"})
    @patch('app.db.postgres_client.postgres_client.get_or_create_website')
    @patch('app.db.postgres_client.postgres_client.get_website_insights')
    def test_query_endpoint_website_not_analyzed(self, mock_insights, mock_get_website):
        """Test query endpoint when website hasn't been analyzed"""
        mock_get_website.return_value = 1
        mock_insights.return_value = None  # Website not analyzed
        
        response = self.client.post(
            "/website/query",
            json={
                "url": "https://example.com",
                "query": "What services do they offer?"
            },
            headers=self.headers
        )
        
        assert response.status_code == 404
        assert "not analyzed" in response.json()["detail"]
    
    def test_query_endpoint_missing_auth(self):
        """Test query endpoint without authentication"""
        response = self.client.post(
            "/website/query",
            json={"url": "https://example.com", "query": "Test question"}
        )
        
        assert response.status_code == 401
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__])
