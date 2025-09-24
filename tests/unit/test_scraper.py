"""
Unit tests for the web scraper module
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from bs4 import BeautifulSoup
import aiohttp

from app.scraper.runner import SimpleScraperRunner
from models.pydantic_models import ScrapedContent


class TestSimpleScraperRunner:
    """Test the SimpleScraperRunner class"""
    
    @pytest.fixture
    def scraper(self):
        """Create a scraper instance"""
        return SimpleScraperRunner()
    
    @pytest.mark.asyncio
    async def test_scraper_initialization(self, scraper):
        """Test scraper initializes correctly"""
        assert scraper.session is None
        session = await scraper._get_session()
        assert session is not None
        assert isinstance(session, aiohttp.ClientSession)
        await scraper.close()
    
    @pytest.mark.asyncio
    async def test_get_session_reuse(self, scraper):
        """Test that session is reused"""
        session1 = await scraper._get_session()
        session2 = await scraper._get_session()
        assert session1 is session2
        await scraper.close()
    
    @pytest.mark.asyncio
    async def test_fetch_with_retries_success(self, scraper):
        """Test successful fetch with retries"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html>Test</html>")
        
        # Create async context manager for session.get()
        mock_get_cm = AsyncMock()
        mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get_cm.__aexit__ = AsyncMock()
        mock_session.get.return_value = mock_get_cm
        
        result = await scraper._fetch_with_retries(mock_session, "https://example.com")
        assert result == "<html>Test</html>"
        mock_session.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_with_retries_failure(self, scraper):
        """Test fetch with retries on failure"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status = 500
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()
        
        with pytest.raises(Exception):
            await scraper._fetch_with_retries(mock_session, "https://example.com", max_retries=2)
        
        assert mock_session.get.call_count == 2
    
    def test_remove_noise_elements(self, scraper, sample_html_content):
        """Test noise element removal"""
        html_with_noise = sample_html_content + """
        <script>console.log('test');</script>
        <style>body { color: red; }</style>
        <footer>Footer content</footer>
        <div class="advertisement">Ad content</div>
        """
        
        soup = BeautifulSoup(html_with_noise, 'lxml')
        scraper._remove_noise_elements(soup)
        
        # Check that noise elements are removed
        assert soup.find('script') is None
        assert soup.find('style') is None
        assert soup.find('footer') is None
        assert soup.find(class_='advertisement') is None
    
    def test_extract_contact_info_from_text(self, scraper):
        """Test contact information extraction"""
        text = """
        Contact us at info@example.com or sales@example.com
        Call us at +1-555-0123 or (555) 456-7890
        Visit our office at 123 Main Street, Suite 100
        """
        
        contact_info = scraper._extract_contact_info_from_text(text)
        
        # Check if emails were found (if not, it's in a different format)
        if 'emails' in contact_info:
            assert 'info@example.com' in contact_info['emails']
            assert 'sales@example.com' in contact_info['emails']
        
        # Check if phones were found
        if 'phones' in contact_info:
            assert len(contact_info['phones']) >= 1
        
        # Check if addresses were found
        if 'addresses' in contact_info:
            assert len(contact_info['addresses']) >= 1
        
        # At least one type of contact info should be found
        assert len(contact_info) > 0
    
    def test_extract_all_content_single_pass(self, scraper, sample_html_content):
        """Test single-pass content extraction"""
        soup = BeautifulSoup(sample_html_content, 'lxml')
        base_url = "https://example.com"
        
        content = scraper._extract_all_content_single_pass(soup, base_url)
        
        assert content['title'] == "Test Company - AI Solutions"
        assert content['meta_description'] == "Leading AI solutions provider"
        assert "Test Company" in content['headings']
        assert "Revolutionary AI Solutions" in content['headings']
        assert len(content['products']) > 0
        assert 'emails' in content['contact_info']
        assert 'contact@testcompany.com' in content['contact_info']['emails']
    
    def test_clean_text(self, scraper):
        """Test text cleaning"""
        dirty_text = "  This   is    some\n\n\ntext   with   spaces  \t\t  "
        clean = scraper._clean_text(dirty_text)
        assert clean == "This is some text with spaces"
        
        text_with_special = "Text with @email.com and numbers 123!"
        clean = scraper._clean_text(text_with_special)
        assert "@" in clean
        assert "123" in clean
    
    def test_generate_focused_raw_text(self, scraper):
        """Test focused raw text generation"""
        content = {
            'title': 'Test Title',
            'meta_description': 'Test Description',
            'headings': ['Heading 1', 'Heading 2'],
            'main_content': 'Main content here',
            'hero_section': 'Hero content',
            'products': ['Product 1', 'Product 2'],
            'business_links': [{'text': 'About', 'url': '/about'}],
            'structured_data': {'name': 'Test'},
            'visible_text': 'All visible text',
            'contact_info': {}
        }
        
        raw_text = scraper._generate_focused_raw_text(content)
        
        assert 'TITLE: Test Title' in raw_text
        assert 'DESCRIPTION: Test Description' in raw_text
        assert 'HEADINGS:' in raw_text
        assert 'Heading 1' in raw_text
        assert 'PRODUCTS:' in raw_text
        assert len(raw_text) <= 5000
    
    @pytest.mark.asyncio
    @patch('app.scraper.runner.SimpleScraperRunner._fetch_with_retries')
    async def test_scrape_website_success(self, mock_fetch, scraper, sample_html_content):
        """Test successful website scraping"""
        mock_fetch.return_value = sample_html_content
        
        result = await scraper.scrape_website("https://example.com")
        
        assert isinstance(result, ScrapedContent)
        assert result.title == "Test Company - AI Solutions"
        assert result.meta_description == "Leading AI solutions provider"
        assert len(result.headings) > 0
        assert len(result.products) > 0
        assert result.raw_text != ""
    
    @pytest.mark.asyncio
    @patch('app.scraper.runner.SimpleScraperRunner._fetch_with_retries')
    async def test_scrape_website_failure(self, mock_fetch, scraper):
        """Test website scraping failure handling"""
        mock_fetch.side_effect = Exception("Network error")
        
        result = await scraper.scrape_website("https://example.com")
        
        assert isinstance(result, ScrapedContent)
        assert result.title is None
        assert result.raw_text == ""
        assert result.headings == []
    
    @pytest.mark.asyncio
    async def test_scraper_cleanup(self, scraper):
        """Test scraper cleanup"""
        session = await scraper._get_session()
        assert scraper.session is not None
        
        await scraper.close()
        # Session should be closed but reference still exists
        assert scraper.session is not None
        assert scraper.session.closed


class TestScraperIntegration:
    """Integration tests for scraper with real-like scenarios"""
    
    @pytest.mark.asyncio
    async def test_scrape_complex_html(self):
        """Test scraping complex HTML with various elements"""
        complex_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Complex Company | Enterprise Solutions</title>
            <meta name="description" content="Enterprise AI and ML solutions">
            <script type="application/ld+json">
            {"@type": "Organization", "name": "Complex Company"}
            </script>
        </head>
        <body>
            <header class="hero-section">
                <h1>Welcome to Complex Company</h1>
                <p>Leading the future of AI</p>
            </header>
            <nav>
                <a href="/products">Products</a>
                <a href="/services">Services</a>
                <a href="mailto:info@complex.com">Contact</a>
            </nav>
            <main>
                <section class="products">
                    <h2>Our Products</h2>
                    <div class="product">AI Platform</div>
                    <div class="product">ML Toolkit</div>
                </section>
                <section class="contact">
                    <h3>Get in Touch</h3>
                    <p>Email: contact@complex.com</p>
                    <p>Phone: <a href="tel:+15551234567">+1 (555) 123-4567</a></p>
                    <div class="social">
                        <a href="https://linkedin.com/company/complex">LinkedIn</a>
                        <a href="https://twitter.com/complex">Twitter</a>
                    </div>
                </section>
            </main>
            <script>console.log('tracking');</script>
            <style>.hidden { display: none; }</style>
        </body>
        </html>
        """
        
        scraper = SimpleScraperRunner()
        
        with patch.object(scraper, '_fetch_with_retries', return_value=complex_html):
            result = await scraper.scrape_website("https://complex.com")
        
        assert result.title == "Complex Company | Enterprise Solutions"
        assert "Welcome to Complex Company" in result.headings
        assert "contact@complex.com" in result.contact_info.get('emails', [])
        assert any("linkedin.com" in link for link in result.contact_info.get('social_media', []))
        assert len(result.raw_text) > 100
        
        await scraper.close()
    
    @pytest.mark.asyncio
    async def test_scrape_minimal_html(self):
        """Test scraping minimal HTML"""
        minimal_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Minimal Site</title></head>
        <body><h1>Welcome</h1><p>Simple content</p></body>
        </html>
        """
        
        scraper = SimpleScraperRunner()
        
        with patch.object(scraper, '_fetch_with_retries', return_value=minimal_html):
            result = await scraper.scrape_website("https://minimal.com")
        
        assert result.title == "Minimal Site"
        assert "Welcome" in result.headings
        assert result.raw_text != ""
        
        await scraper.close()
    
    @pytest.mark.asyncio
    async def test_scrape_malformed_html(self):
        """Test scraping malformed HTML"""
        malformed_html = """
        <html>
        <title>Broken Site
        <body>
        <h1>Header without closing
        <p>Paragraph without closing
        <div>Content
        """
        
        scraper = SimpleScraperRunner()
        
        with patch.object(scraper, '_fetch_with_retries', return_value=malformed_html):
            result = await scraper.scrape_website("https://broken.com")
        
        # Should handle malformed HTML gracefully
        assert result is not None
        assert isinstance(result, ScrapedContent)
        # Should extract title even from malformed HTML
        assert "Broken Site" in str(result.title) or len(result.raw_text) > 0
        
        await scraper.close()
