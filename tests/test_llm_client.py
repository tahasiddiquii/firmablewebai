import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.llm.llm_client import llm_client
from models.pydantic_models import ScrapedContent


class TestLLMClient:
    """Test cases for the LLM client"""
    
    @pytest.mark.asyncio
    async def test_generate_insights_returns_structured_data(self):
        """Test that insights generation returns properly structured data"""
        scraped_content = ScrapedContent(
            title="Test Company",
            meta_description="A test company",
            headings=["About", "Services"],
            main_content="We provide excellent services",
            hero_section="Welcome to Test Company",
            products=["Service A", "Service B"],
            contact_info={"emails": ["contact@test.com"]},
            raw_text="Full website content"
        )
        
        with patch.object(llm_client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"industry": "Technology", "company_size": "Small", "location": "San Francisco", "USP": "Innovative solutions", "products": ["Service A", "Service B"], "target_audience": "Small businesses", "contact_info": {"emails": ["contact@test.com"]}}'
            mock_create.return_value = mock_response
            
            insights = await llm_client.generate_insights(scraped_content)
            
            assert isinstance(insights, dict)
            assert "industry" in insights
            assert "company_size" in insights
            assert "location" in insights
            assert "USP" in insights
            assert "products" in insights
            assert "target_audience" in insights
            assert "contact_info" in insights
    
    @pytest.mark.asyncio
    async def test_generate_embedding_returns_vector(self):
        """Test that embedding generation returns a vector"""
        with patch.object(llm_client.client.embeddings, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = Mock()
            mock_response.data = [Mock()]
            mock_response.data[0].embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
            mock_create.return_value = mock_response
            
            embedding = await llm_client.generate_embedding("Test text")
            
            assert isinstance(embedding, list)
            assert len(embedding) == 5
            assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_generate_rag_response_returns_answer(self):
        """Test that RAG response generation returns an answer"""
        chunks = ["Chunk 1 content", "Chunk 2 content"]
        history = [{"role": "user", "content": "Previous question"}, {"role": "assistant", "content": "Previous answer"}]
        
        with patch.object(llm_client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "This is the answer based on the chunks."
            mock_create.return_value = mock_response
            
            answer = await llm_client.generate_rag_response("Test question", chunks, history)
            
            assert isinstance(answer, str)
            assert len(answer) > 0
    
    def test_chunk_text_splits_correctly(self):
        """Test that text chunking works correctly"""
        long_text = "This is a very long text that should be split into multiple chunks. " * 50
        
        chunks = llm_client.chunk_text(long_text, chunk_size=100, overlap=20)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 for chunk in chunks)
    
    def test_chunk_text_handles_short_text(self):
        """Test that short text is not chunked"""
        short_text = "Short text"
        
        chunks = llm_client.chunk_text(short_text, chunk_size=100)
        
        assert chunks == [short_text]
    
    @pytest.mark.asyncio
    async def test_llm_client_handles_errors(self):
        """Test that LLM client handles API errors gracefully"""
        with patch.object(llm_client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            scraped_content = ScrapedContent(
                title="Test",
                meta_description="Test",
                headings=[],
                main_content="Test",
                hero_section="Test",
                products=[],
                contact_info={},
                raw_text="Test"
            )
            
            insights = await llm_client.generate_insights(scraped_content)
            
            # Should return default insights on error
            assert insights["industry"] == "Unknown"
            assert insights["products"] == []


if __name__ == "__main__":
    pytest.main([__file__])
