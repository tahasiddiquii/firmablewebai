import scrapy
from scrapy import Request
from scrapy.http import Response
from typing import Dict, Any, List
import re
from urllib.parse import urljoin, urlparse


class HomepageSpider(scrapy.Spider):
    name = 'homepage_spider'
    
    def __init__(self, url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [url]
        self.allowed_domains = [urlparse(url).netloc]
    
    def parse(self, response: Response) -> Dict[str, Any]:
        """Extract homepage content"""
        
        # Extract title
        title = response.css('title::text').get()
        if title:
            title = title.strip()
        
        # Extract meta description
        meta_description = response.css('meta[name="description"]::attr(content)').get()
        if not meta_description:
            meta_description = response.css('meta[property="og:description"]::attr(content)').get()
        
        # Extract headings
        headings = []
        for selector in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            heading_texts = response.css(f'{selector}::text').getall()
            headings.extend([h.strip() for h in heading_texts if h.strip()])
        
        # Extract main content (try different selectors)
        main_content = self._extract_main_content(response)
        
        # Extract hero section (usually the first prominent section)
        hero_section = self._extract_hero_section(response)
        
        # Extract products/services
        products = self._extract_products(response)
        
        # Extract contact information
        contact_info = self._extract_contact_info(response)
        
        # Get all text content
        raw_text = self._extract_raw_text(response)
        
        return {
            'title': title,
            'meta_description': meta_description,
            'headings': headings,
            'main_content': main_content,
            'hero_section': hero_section,
            'products': products,
            'contact_info': contact_info,
            'raw_text': raw_text
        }
    
    def _extract_main_content(self, response: Response) -> str:
        """Extract main content using various selectors"""
        content_selectors = [
            'main',
            'article',
            '.content',
            '.main-content',
            '.page-content',
            '#content',
            '.container .row',
            'body'
        ]
        
        for selector in content_selectors:
            content = response.css(selector)
            if content:
                text = ' '.join(content.css('::text').getall())
                if len(text.strip()) > 100:  # Ensure we have substantial content
                    return self._clean_text(text)
        
        return ""
    
    def _extract_hero_section(self, response: Response) -> str:
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
            hero = response.css(selector)
            if hero:
                text = ' '.join(hero.css('::text').getall())
                if text.strip():
                    return self._clean_text(text)
        
        return ""
    
    def _extract_products(self, response: Response) -> List[str]:
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
            items = response.css(selector)
            for item in items:
                text = ' '.join(item.css('::text').getall())
                if text.strip() and len(text.strip()) > 10:
                    products.append(self._clean_text(text))
        
        # Also look for product names in headings
        for heading in response.css('h1, h2, h3, h4, h5, h6::text').getall():
            heading = heading.strip()
            if heading and len(heading) < 100:  # Reasonable product name length
                products.append(heading)
        
        return list(set(products))  # Remove duplicates
    
    def _extract_contact_info(self, response: Response) -> Dict[str, Any]:
        """Extract contact information"""
        contact_info = {}
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, response.text)
        if emails:
            contact_info['emails'] = list(set(emails))
        
        # Extract phone numbers
        phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phones = re.findall(phone_pattern, response.text)
        if phones:
            contact_info['phones'] = [''.join(phone) for phone in phones]
        
        # Extract addresses (basic pattern)
        address_pattern = r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl)'
        addresses = re.findall(address_pattern, response.text)
        if addresses:
            contact_info['addresses'] = addresses
        
        # Extract social media links
        social_links = []
        for link in response.css('a[href*="facebook"], a[href*="twitter"], a[href*="linkedin"], a[href*="instagram"]::attr(href)').getall():
            social_links.append(link)
        if social_links:
            contact_info['social_links'] = social_links
        
        return contact_info
    
    def _extract_raw_text(self, response: Response) -> str:
        """Extract all text content from the page"""
        # Remove script and style elements
        for script in response.css('script, style'):
            script.extract()
        
        # Get all text
        text = ' '.join(response.css('::text').getall())
        return self._clean_text(text)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        return text.strip()
