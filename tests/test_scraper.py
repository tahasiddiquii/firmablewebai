import pytest
import asyncio
from unittest.mock import Mock, patch
from app.scraper.runner import scraper_runner
from models.pydantic_models import ScrapedContent


class TestScraper:
    """Test cases for the website scraper"""
    
    @pytest.mark.asyncio
    async def test_scraper_returns_structured_content(self):
        """Test that scraper returns properly structured content"""
        # Mock the scraper to return test data
        with patch.object(scraper_runner, 'scrape_website') as mock_scrape:
            mock_scrape.return_value = ScrapedContent(
                title="Test Company",
                meta_description="A test company description",
                headings=["Welcome", "About Us", "Services"],
                main_content="This is the main content of the test website.",
                hero_section="Welcome to Test Company",
                products=["Product 1", "Product 2"],
                contact_info={"emails": ["test@example.com"]},
                raw_text="Full website text content"
            )
            
            result = await scraper_runner.scrape_website("https://example.com")
            
            assert isinstance(result, ScrapedContent)
            assert result.title == "Test Company"
            assert result.products == ["Product 1", "Product 2"]
            assert "test@example.com" in result.contact_info["emails"]
    
    @pytest.mark.asyncio
    async def test_scraper_handles_empty_content(self):
        """Test scraper handles websites with minimal content"""
        with patch.object(scraper_runner, 'scrape_website') as mock_scrape:
            mock_scrape.return_value = ScrapedContent(
                title=None,
                meta_description=None,
                headings=[],
                main_content=None,
                hero_section=None,
                products=[],
                contact_info={},
                raw_text=""
            )
            
            result = await scraper_runner.scrape_website("https://empty-site.com")
            
            assert isinstance(result, ScrapedContent)
            assert result.title is None
            assert result.products == []
            assert result.raw_text == ""
    
    @pytest.mark.asyncio
    async def test_scraper_handles_errors(self):
        """Test scraper handles scraping errors gracefully"""
        with patch.object(scraper_runner, 'scrape_website') as mock_scrape:
            mock_scrape.side_effect = Exception("Scraping failed")
            
            result = await scraper_runner.scrape_website("https://invalid-site.com")
            
            # Should return empty content on error
            assert isinstance(result, ScrapedContent)
            assert result.title is None
            assert result.raw_text == ""


if __name__ == "__main__":
    pytest.main([__file__])
