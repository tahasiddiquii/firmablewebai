"""
Unit tests for the LLM client module
"""

import pytest
import json
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

from app.llm.llm_client import LLMClient
from models.pydantic_models import ScrapedContent


class TestLLMClient:
    """Test the LLMClient class"""
    
    @pytest.fixture
    def llm_client_no_key(self, monkeypatch):
        """Create LLM client without API key"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        return LLMClient()
    
    @pytest.fixture
    def llm_client_with_key(self, monkeypatch):
        """Create LLM client with mocked API key"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        with patch('app.llm.llm_client.AsyncOpenAI'):
            client = LLMClient()
            client.client = Mock()
            client.available = True
            return client
    
    def test_initialization_without_key(self, llm_client_no_key):
        """Test LLM client initialization without API key"""
        assert llm_client_no_key.client is None
        assert llm_client_no_key.available is False
        assert llm_client_no_key.embedding_model is None
    
    def test_initialization_with_key(self, monkeypatch):
        """Test LLM client initialization with API key"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        
        with patch('app.llm.llm_client.AsyncOpenAI') as mock_openai:
            client = LLMClient()
            assert client.client is not None
            assert client.available is True
            assert client.embedding_model == "text-embedding-3-large"
            mock_openai.assert_called_once_with(api_key="test-key-123")
    
    @pytest.mark.asyncio
    async def test_generate_insights_no_client(self, llm_client_no_key, sample_scraped_content):
        """Test generate_insights without OpenAI client"""
        with pytest.raises(Exception, match="OpenAI client not available"):
            await llm_client_no_key.generate_insights(sample_scraped_content)
    
    @pytest.mark.asyncio
    async def test_generate_insights_success(self, llm_client_with_key, sample_scraped_content):
        """Test successful insights generation"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "industry": "Technology",
            "company_size": "Small (11-50)",
            "location": "San Francisco",
            "USP": "Innovative AI solutions",
            "products": ["Product A", "Product B"],
            "target_audience": "Enterprises",
            "contact_info": {"emails": ["test@example.com"]}
        })
        
        llm_client_with_key.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        insights = await llm_client_with_key.generate_insights(sample_scraped_content)
        
        assert insights["industry"] == "Technology"
        assert insights["company_size"] == "Small (11-50)"
        assert insights["location"] == "San Francisco"
        assert isinstance(insights["products"], list)
        assert len(insights["products"]) == 2
        assert insights["contact_info"]["emails"] == ["test@example.com"]
    
    @pytest.mark.asyncio
    async def test_generate_insights_with_questions(self, llm_client_with_key, sample_scraped_content):
        """Test insights generation with custom questions"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "industry": "AI Technology",
            "company_size": None,
            "location": None,
            "USP": "Custom AI solutions",
            "products": [],
            "target_audience": None,
            "contact_info": {}
        })
        
        llm_client_with_key.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        questions = ["What is their pricing model?", "Who are their competitors?"]
        insights = await llm_client_with_key.generate_insights(sample_scraped_content, questions)
        
        # Verify the API was called with questions in the prompt
        call_args = llm_client_with_key.client.chat.completions.create.call_args
        prompt = call_args[1]['messages'][1]['content']
        assert "What is their pricing model?" in prompt
        assert "Who are their competitors?" in prompt
    
    @pytest.mark.asyncio
    async def test_generate_insights_malformed_response(self, llm_client_with_key, sample_scraped_content):
        """Test insights generation with malformed JSON response"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is not valid JSON"
        
        llm_client_with_key.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        insights = await llm_client_with_key.generate_insights(sample_scraped_content)
        
        # Should return default values on error
        assert insights["industry"] == "Business Services"
        assert insights["company_size"] == "Not specified"
        assert insights["products"] == []
    
    @pytest.mark.asyncio
    async def test_generate_insights_location_detection(self, llm_client_with_key):
        """Test location detection in insights"""
        content = ScrapedContent(
            title="Australian Tech Company",
            meta_description="Leading tech in Australia and NZ",
            headings=["Sydney Office", "Melbourne Branch"],
            main_content="Serving the Australian market",
            hero_section="",
            products=[],
            contact_info={},
            raw_text="Based in Australia with offices in Sydney and Melbourne"
        )
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "industry": "Technology",
            "company_size": None,
            "location": "Australia",
            "USP": "Local tech solutions",
            "products": [],
            "target_audience": "Australian businesses",
            "contact_info": {}
        })
        
        llm_client_with_key.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        insights = await llm_client_with_key.generate_insights(content)
        
        # Check that location hints were included in prompt
        call_args = llm_client_with_key.client.chat.completions.create.call_args
        prompt = call_args[1]['messages'][1]['content']
        assert "Australia" in prompt or "Geographic focus" in prompt
    
    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, llm_client_with_key):
        """Test successful embedding generation"""
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        llm_client_with_key.client.embeddings.create = AsyncMock(return_value=mock_response)
        
        embedding = await llm_client_with_key.generate_embedding("Test text")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 5
        assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
    
    @pytest.mark.asyncio
    async def test_generate_embedding_no_client(self, llm_client_no_key):
        """Test embedding generation without client"""
        embedding = await llm_client_no_key.generate_embedding("Test text")
        assert embedding == []
    
    @pytest.mark.asyncio
    async def test_generate_embedding_error(self, llm_client_with_key):
        """Test embedding generation with error"""
        llm_client_with_key.client.embeddings.create = AsyncMock(side_effect=Exception("API Error"))
        
        embedding = await llm_client_with_key.generate_embedding("Test text")
        assert embedding == []
    
    @pytest.mark.asyncio
    async def test_generate_rag_response_success(self, llm_client_with_key):
        """Test successful RAG response generation"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This company provides AI solutions for businesses."
        
        llm_client_with_key.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        query = "What does this company do?"
        chunks = ["The company offers AI products", "Machine learning solutions"]
        history = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
        
        response = await llm_client_with_key.generate_rag_response(query, chunks, history)
        
        assert response == "This company provides AI solutions for businesses."
        
        # Verify prompt construction
        call_args = llm_client_with_key.client.chat.completions.create.call_args
        prompt = call_args[1]['messages'][1]['content']
        assert query in prompt
        assert chunks[0] in prompt
        assert "Hello" in prompt  # From history
    
    @pytest.mark.asyncio
    async def test_generate_rag_response_no_client(self, llm_client_no_key):
        """Test RAG response without client"""
        response = await llm_client_no_key.generate_rag_response(
            "Query", ["chunk"], []
        )
        assert "not available" in response.lower()
    
    @pytest.mark.asyncio
    async def test_generate_rag_response_error(self, llm_client_with_key):
        """Test RAG response with error"""
        llm_client_with_key.client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        response = await llm_client_with_key.generate_rag_response(
            "Query", ["chunk"], []
        )
        assert "error" in response.lower()
    
    def test_chunk_text_single_chunk(self, llm_client_with_key):
        """Test text chunking with text smaller than chunk size"""
        text = "This is a short text"
        chunks = llm_client_with_key.chunk_text(text, chunk_size=100)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_multiple_chunks(self, llm_client_with_key):
        """Test text chunking with overlap"""
        text = "A" * 1000  # 1000 character text
        chunks = llm_client_with_key.chunk_text(text, chunk_size=300, overlap=50)
        
        assert len(chunks) > 1
        # First chunk should be 300 chars
        assert len(chunks[0]) == 300
        # Check overlap exists
        assert chunks[0][-50:] == chunks[1][:50]
    
    def test_chunk_text_no_overlap(self, llm_client_with_key):
        """Test text chunking without overlap"""
        text = "A" * 1000
        chunks = llm_client_with_key.chunk_text(text, chunk_size=250, overlap=0)
        
        assert len(chunks) == 4  # 1000 / 250 = 4
        # Check that chunks are sequential without overlap
        for i in range(len(chunks) - 1):
            # With no overlap, end of one chunk should connect to start of next
            assert len(chunks[i]) == 250  # Each chunk should be exactly 250 chars


class TestLLMClientIntegration:
    """Integration tests for LLM client"""
    
    @pytest.mark.asyncio
    @pytest.mark.requires_api_key
    async def test_full_insights_flow(self, monkeypatch):
        """Test full insights generation flow (requires API key)"""
        # This test only runs if OPENAI_API_KEY is set
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")
        
        monkeypatch.setenv("OPENAI_API_KEY", api_key)
        
        client = LLMClient()
        assert client.available
        
        content = ScrapedContent(
            title="Example Tech Company",
            meta_description="We provide cloud solutions",
            headings=["About Us", "Our Services", "Contact"],
            main_content="Leading cloud infrastructure provider",
            hero_section="Transform your business with cloud",
            products=["Cloud Storage", "Cloud Computing"],
            contact_info={"emails": ["info@example.com"]},
            raw_text="Example Tech Company provides cloud solutions..."
        )
        
        insights = await client.generate_insights(content)
        
        assert "industry" in insights
        assert insights["industry"] != ""
        assert "products" in insights
        assert isinstance(insights["products"], list)
    
    @pytest.mark.asyncio
    async def test_insights_cleaning_edge_cases(self):
        """Test insights cleaning with edge cases"""
        with patch('app.llm.llm_client.AsyncOpenAI'):
            client = LLMClient()
            client.available = True
            
            # Test with products as dict objects
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "industry": "",  # Empty industry
                "products": [{"name": "Product A"}, {"name": "Product B"}],  # Dict products
                "contact_info": "not a dict",  # Wrong type
                "company_size": None,
                "location": None,
                "USP": None,
                "target_audience": None
            })
            
            client.client = Mock()
            client.client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            content = Mock(spec=ScrapedContent)
            content.title = "Test"
            content.meta_description = "Test"
            content.headings = []
            content.main_content = ""
            content.hero_section = ""
            content.products = []
            content.contact_info = {}
            content.raw_text = "Test"
            
            insights = await client.generate_insights(content)
            
            # Check cleaning worked
            assert insights["industry"] == "Business Services"  # Fallback for empty
            assert insights["products"] == ["Product A", "Product B"]  # Converted from dict
            assert isinstance(insights["contact_info"], dict)  # Converted to dict
            assert "emails" in insights["contact_info"]
            assert "phones" in insights["contact_info"]
            assert "social_media" in insights["contact_info"]
