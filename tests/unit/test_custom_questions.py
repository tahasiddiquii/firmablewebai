"""Unit tests for custom questions functionality"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from models.pydantic_models import InsightsResponse, ScrapedContent
from app.llm.llm_client import LLMClient
import json


class TestCustomQuestions:
    """Test custom questions handling in insights generation"""
    
    @pytest.fixture
    def llm_client(self, monkeypatch):
        """Create LLM client with mocked OpenAI"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        return LLMClient()
    
    @pytest.fixture
    def sample_scraped_content(self):
        """Create sample scraped content"""
        return ScrapedContent(
            title="Example Company",
            meta_description="We provide innovative solutions",
            headings=["About Us", "Products", "Contact"],
            main_content="Example Company is a leader in technology solutions.",
            hero_section="Welcome to Example Company",
            products=["Product A", "Product B"],
            contact_info={"email": "info@example.com"},
            raw_text="Full website content here..."
        )
    
    @pytest.mark.asyncio
    async def test_generate_insights_with_custom_questions(self, llm_client, sample_scraped_content):
        """Test that custom questions are included in the prompt and response"""
        custom_questions = [
            "What is the company's mission?",
            "Do they offer cloud services?",
            "What is their pricing model?"
        ]
        
        # Mock the OpenAI response with custom answers
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "industry": "Technology",
            "company_size": "Medium",
            "location": "San Francisco, CA",
            "USP": "Innovative technology solutions",
            "products": ["Product A", "Product B"],
            "target_audience": "Enterprise clients",
            "contact_info": {"emails": ["info@example.com"]},
            "custom_answers": {
                "What is the company's mission?": "To provide innovative technology solutions that transform businesses.",
                "Do they offer cloud services?": "Yes, they offer comprehensive cloud infrastructure and SaaS solutions.",
                "What is their pricing model?": "They use a subscription-based pricing model with multiple tiers."
            }
        })
        
        with patch.object(llm_client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await llm_client.generate_insights(sample_scraped_content, custom_questions)
            
            # Verify the API was called
            mock_create.assert_called_once()
            
            # Check that custom questions were included in the prompt
            call_args = mock_create.call_args
            prompt_content = call_args[1]['messages'][1]['content']
            
            assert "CUSTOM QUESTIONS TO ANSWER:" in prompt_content
            for question in custom_questions:
                assert question in prompt_content
            
            # Verify the response includes custom answers
            assert "custom_answers" in result
            assert len(result["custom_answers"]) == 3
            assert "What is the company's mission?" in result["custom_answers"]
            assert "Do they offer cloud services?" in result["custom_answers"]
            assert "What is their pricing model?" in result["custom_answers"]
    
    @pytest.mark.asyncio
    async def test_generate_insights_without_custom_questions(self, llm_client, sample_scraped_content):
        """Test that insights work normally without custom questions"""
        
        # Mock the OpenAI response without custom answers
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "industry": "Technology",
            "company_size": "Medium",
            "location": "San Francisco, CA",
            "USP": "Innovative technology solutions",
            "products": ["Product A", "Product B"],
            "target_audience": "Enterprise clients",
            "contact_info": {"emails": ["info@example.com"]}
        })
        
        with patch.object(llm_client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await llm_client.generate_insights(sample_scraped_content, [])
            
            # Verify the API was called
            mock_create.assert_called_once()
            
            # Check that no custom questions section appears in the prompt
            call_args = mock_create.call_args
            prompt_content = call_args[1]['messages'][1]['content']
            
            assert "CUSTOM QUESTIONS TO ANSWER:" not in prompt_content
            
            # Verify the response doesn't include custom answers
            assert "custom_answers" not in result or result.get("custom_answers") is None
    
    @pytest.mark.asyncio
    async def test_custom_questions_json_format(self, llm_client, sample_scraped_content):
        """Test that the JSON format for custom questions is correctly generated"""
        custom_questions = [
            "Question with special chars: What's the cost?",
            "Question with quotes: Do they offer \"enterprise\" plans?"
        ]
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "industry": "Technology",
            "company_size": "Medium",
            "location": "San Francisco, CA",
            "USP": "Innovative solutions",
            "products": ["Product A"],
            "target_audience": "Enterprises",
            "contact_info": {},
            "custom_answers": {
                "Question with special chars: What's the cost?": "Pricing starts at $99/month",
                "Question with quotes: Do they offer \"enterprise\" plans?": "Yes, custom enterprise plans available"
            }
        })
        
        with patch.object(llm_client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await llm_client.generate_insights(sample_scraped_content, custom_questions)
            
            # Check that the prompt includes properly formatted questions
            call_args = mock_create.call_args
            prompt_content = call_args[1]['messages'][1]['content']
            
            # Verify custom answers are properly formatted
            assert "custom_answers" in result
            assert len(result["custom_answers"]) == 2
    
    def test_insights_response_model_with_custom_answers(self):
        """Test that InsightsResponse model accepts custom_answers field"""
        
        response_data = {
            "industry": "Technology",
            "company_size": "Large",
            "location": "New York, NY",
            "USP": "Leading provider",
            "products": ["Service A", "Service B"],
            "target_audience": "SMBs",
            "contact_info": {"emails": ["contact@example.com"]},
            "custom_answers": {
                "Q1": "Answer 1",
                "Q2": "Answer 2"
            }
        }
        
        # This should not raise a validation error
        response = InsightsResponse(**response_data)
        
        assert response.custom_answers is not None
        assert len(response.custom_answers) == 2
        assert response.custom_answers["Q1"] == "Answer 1"
        assert response.custom_answers["Q2"] == "Answer 2"
    
    def test_insights_response_model_without_custom_answers(self):
        """Test that InsightsResponse model works without custom_answers field"""
        
        response_data = {
            "industry": "Technology",
            "company_size": "Large",
            "location": "New York, NY",
            "USP": "Leading provider",
            "products": ["Service A"],
            "target_audience": "SMBs",
            "contact_info": {}
        }
        
        # This should not raise a validation error
        response = InsightsResponse(**response_data)
        
        assert response.custom_answers is None
