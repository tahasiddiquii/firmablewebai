import asyncio
import aiohttp
import re
from typing import Dict, Any, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.pydantic_models import ScrapedContent


class SimpleScraperRunner:
    def __init__(self):
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'User-Agent': 'FirmableWebAI/1.0 (+https://firmablewebai.com)'
                }
            )
        return self.session
    
    async def scrape_website(self, url: str) -> ScrapedContent:
        """Scrape a website and return structured content"""
        try:
            session = await self._get_session()
            
            # Fetch the webpage
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extract structured data
                title = self._extract_title(soup)
                meta_description = self._extract_meta_description(soup)
                headings = self._extract_headings(soup)
                main_content = self._extract_main_content(soup)
                hero_section = self._extract_hero_section(soup)
                products = self._extract_products(soup)
                contact_info = self._extract_contact_info(soup, html)
                raw_text = self._extract_raw_text(soup)
                
                return ScrapedContent(
                    title=title,
                    meta_description=meta_description,
                    headings=headings,
                    main_content=main_content,
                    hero_section=hero_section,
                    products=products,
                    contact_info=contact_info,
                    raw_text=raw_text
                )
                
        except Exception as e:
            print(f"Error scraping website {url}: {e}")
            # Return empty content on error
            return ScrapedContent(
                title=None,
                meta_description=None,
                headings=[],
                main_content=None,
                hero_section=None,
                products=[],
                contact_info={},
                raw_text=""
            )
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else None
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta = soup.find('meta', attrs={'name': 'description'})
        if not meta:
            meta = soup.find('meta', attrs={'property': 'og:description'})
        return meta.get('content', '').strip() if meta else None
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[str]:
        """Extract all headings"""
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = tag.get_text().strip()
            if text:
                headings.append(text)
        return headings
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content using various selectors"""
        content_selectors = [
            'main',
            'article',
            '.content',
            '.main-content',
            '.page-content',
            '#content',
            '.container',
            'body'
        ]
        
        for selector in content_selectors:
            if selector.startswith('.') or selector.startswith('#'):
                elements = soup.select(selector)
            else:
                elements = soup.find_all(selector)
            
            for element in elements:
                text = element.get_text().strip()
                if len(text) > 200:  # Ensure substantial content
                    return self._clean_text(text)
        
        return ""
    
    def _extract_hero_section(self, soup: BeautifulSoup) -> str:
        """Extract hero section content"""
        hero_selectors = [
            '.hero',
            '.hero-section',
            '.banner',
            '.jumbotron',
            '.hero-banner',
            'header .container',
            '.intro'
        ]
        
        for selector in hero_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) > 50:
                    return self._clean_text(text)
        
        return ""
    
    def _extract_products(self, soup: BeautifulSoup) -> List[str]:
        """Extract products/services mentioned"""
        products = []
        
        # Look for product-related sections
        product_selectors = [
            '.product',
            '.service',
            '.feature',
            '.offering',
            '[class*="product"]',
            '[class*="service"]',
            '[class*="feature"]'
        ]
        
        for selector in product_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) > 10 and len(text) < 200:
                    products.append(self._clean_text(text))
        
        # Also look for product names in headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = heading.get_text().strip()
            if text and len(text) < 100:  # Reasonable product name length
                products.append(text)
        
        return list(set(products))  # Remove duplicates
    
    def _extract_contact_info(self, soup: BeautifulSoup, html: str) -> Dict[str, Any]:
        """Extract contact information"""
        contact_info = {}
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, html)
        if emails:
            contact_info['emails'] = list(set(emails))
        
        # Extract phone numbers
        phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phones = re.findall(phone_pattern, html)
        if phones:
            contact_info['phones'] = [''.join(phone) for phone in phones]
        
        # Extract addresses (basic pattern)
        address_pattern = r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl)'
        addresses = re.findall(address_pattern, html)
        if addresses:
            contact_info['addresses'] = addresses
        
        # Extract social media links
        social_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(social in href for social in ['facebook', 'twitter', 'linkedin', 'instagram']):
                social_links.append(href)
        if social_links:
            contact_info['social_links'] = social_links
        
        return contact_info
    
    def _extract_raw_text(self, soup: BeautifulSoup) -> str:
        """Extract all text content from the page"""
        text = soup.get_text()
        return self._clean_text(text)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        return text.strip()
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()


# Global instance
scraper_runner = SimpleScraperRunner()
