import asyncio
import aiohttp
import re
import json
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Comment
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.pydantic_models import ScrapedContent


class SimpleScraperRunner:
    def __init__(self):
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session with comprehensive headers"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=45)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                }
            )
        return self.session
    
    async def _fetch_with_retries(self, session: aiohttp.ClientSession, url: str, max_retries: int = 3) -> str:
        """Fetch webpage with retries and different strategies"""
        for attempt in range(max_retries):
            try:
                print(f"🌐 Attempt {attempt + 1} to fetch: {url}")
                async with session.get(url, allow_redirects=True) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status in [301, 302, 303, 307, 308]:
                        # Handle redirects manually if needed
                        redirect_url = response.headers.get('Location')
                        if redirect_url:
                            print(f"🔄 Following redirect to: {redirect_url}")
                            continue
                    else:
                        print(f"⚠️ HTTP {response.status} on attempt {attempt + 1}")
                        if attempt == max_retries - 1:
                            raise Exception(f"HTTP {response.status}")
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(1)  # Wait before retry
        
        raise Exception("Max retries exceeded")
    
    def _remove_noise_elements(self, soup: BeautifulSoup) -> None:
        """Remove noise elements before parsing for better performance and focus"""
        noise_selectors = [
            'script', 'style', 'noscript', 'iframe', 'embed', 'object', 'footer',
            '.advertisement', '.ads', '.cookie-banner', '.popup', '.modal',
            '.social-share', '.comments', '.sidebar', '.footer-links',
            '[class*="ad-"]', '[id*="ad-"]', '[class*="advertisement"]',
            '[class*="banner"]', '[class*="popup"]', '[id*="popup"]',
            '.newsletter-signup', '.subscription', '.tracking', '.gdpr',
            '[class*="cookie"]', '[id*="cookie"]', '.overlay'
        ]
        
        for selector in noise_selectors:
            for element in soup.select(selector):
                element.decompose()
    
    def _extract_contact_info_from_text(self, text: str) -> Dict[str, Any]:
        """Extract contact information from clean text using regex"""
        contact_info = {}
        
        # Extract email addresses from clean text
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            # Remove duplicates and filter out common false positives
            filtered_emails = []
            for email in set(emails):
                if not any(skip in email.lower() for skip in ['example.com', 'test.com', 'placeholder']):
                    filtered_emails.append(email)
            if filtered_emails:
                contact_info['emails'] = filtered_emails
        
        # Extract phone numbers from clean text
        phone_patterns = [
            r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'\+?[1-9]\d{1,14}',  # International format
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'  # US format variations
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if isinstance(matches[0], tuple):
                    phones.extend([''.join(phone) for phone in matches])
                else:
                    phones.extend(matches)
        
        if phones:
            # Clean and deduplicate phone numbers
            clean_phones = []
            for phone in set(phones):
                # Remove common separators and keep only digits and +
                clean_phone = re.sub(r'[^\d+]', '', phone)
                if len(clean_phone) >= 10:  # Minimum valid phone length
                    clean_phones.append(phone)
            if clean_phones:
                contact_info['phones'] = clean_phones
        
        # Extract addresses from clean text
        address_pattern = r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl|Circle|Cir|Court|Ct)'
        addresses = re.findall(address_pattern, text, re.IGNORECASE)
        if addresses:
            contact_info['addresses'] = list(set(addresses))
        
        return contact_info
    
    def _extract_all_content_single_pass(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Single-pass extraction of all content from the cleaned soup"""
        content = {
            'title': None,
            'meta_description': None,
            'headings': [],
            'main_content': '',
            'hero_section': '',
            'products': [],
            'contact_info': {},
            'business_links': [],
            'structured_data': {},
            'visible_text': ''
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            content['title'] = title_tag.get_text().strip()
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if not meta_desc:
            meta_desc = soup.find('meta', attrs={'property': 'og:description'})
        if meta_desc:
            content['meta_description'] = meta_desc.get('content', '').strip()
        
        # Extract structured data (JSON-LD)
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                content['structured_data'] = data
                break  # Take first valid JSON-LD
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # Single traversal for all content extraction
        business_keywords = [
            'about', 'contact', 'services', 'products', 'pricing', 'features',
            'solutions', 'company', 'team', 'careers', 'blog', 'news'
        ]
        
        product_keywords = [
            'product', 'service', 'feature', 'offering', 'solution'
        ]
        
        hero_selectors = [
            '.hero', '.hero-section', '.banner', '.jumbotron', 
            '.hero-banner', 'header .container', '.intro'
        ]
        
        main_content_selectors = [
            'main', 'article', '.content', '.main-content', 
            '.page-content', '#content', '.container'
        ]
        
        # Traverse all elements once
        for element in soup.find_all(True):  # Find all tags
            tag_name = element.name
            element_text = element.get_text().strip()
            element_classes = element.get('class', [])
            element_id = element.get('id', '')
            
            # Extract headings
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'] and element_text:
                content['headings'].append(element_text)
            
            # Extract business links
            if tag_name == 'a' and element.get('href'):
                href = element.get('href')
                link_text = element_text.lower()
                
                if (not href.startswith(('#', 'javascript:', 'mailto:')) and 
                    element_text and 
                    any(keyword in link_text or keyword in href.lower() for keyword in business_keywords)):
                    
                    # Convert relative URLs
                    if href.startswith('/'):
                        href = urljoin(base_url, href)
                    
                    content['business_links'].append({
                        'text': element_text[:100],
                        'url': href
                    })
                    
                    if len(content['business_links']) >= 10:  # Limit
                        break
            
            # Check for hero sections
            if (any(hero_class in ' '.join(element_classes).lower() for hero_class in [cls.strip('.') for cls in hero_selectors]) or
                any(hero_id in element_id.lower() for hero_id in ['hero', 'banner', 'intro'])):
                if element_text and len(element_text) > 50 and not content['hero_section']:
                    content['hero_section'] = self._clean_text(element_text)
            
            # Check for main content
            if (tag_name in ['main', 'article'] or 
                any(main_class in ' '.join(element_classes).lower() for main_class in ['content', 'main-content', 'page-content']) or
                element_id in ['content', 'main-content']):
                if element_text and len(element_text) > 200 and not content['main_content']:
                    content['main_content'] = self._clean_text(element_text)
            
            # Check for products/services
            if (any(prod_keyword in ' '.join(element_classes).lower() for prod_keyword in product_keywords) or
                any(prod_keyword in element_text.lower() for prod_keyword in product_keywords)):
                if element_text and 10 < len(element_text) < 200:
                    content['products'].append(self._clean_text(element_text))
        
        # Extract visible text after cleaning
        content['visible_text'] = soup.get_text(separator=' ', strip=True)
        content['visible_text'] = self._clean_text(content['visible_text'])
        
        # Extract contact info from clean visible text
        content['contact_info'] = self._extract_contact_info_from_text(content['visible_text'])
        
        # Add social media links from contact info extraction
        social_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(social in href.lower() for social in ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube']):
                social_links.append(href)
        if social_links:
            content['contact_info']['social_links'] = social_links[:5]  # Limit to 5
        
        # Remove duplicates and limit sizes
        content['headings'] = list(dict.fromkeys(content['headings']))[:15]  # Remove duplicates, limit to 15
        content['products'] = list(dict.fromkeys(content['products']))[:10]  # Remove duplicates, limit to 10
        
        return content
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-@+]', '', text)
        return text.strip()
    
    def _generate_focused_raw_text(self, content: Dict[str, Any]) -> str:
        """Generate focused business text from extracted content"""
        content_parts = []
        
        # Title and meta (most important)
        if content['title']:
            content_parts.append(f"TITLE: {content['title']}")
        
        if content['meta_description']:
            content_parts.append(f"DESCRIPTION: {content['meta_description']}")
        
        # Key headings (limited)
        if content['headings']:
            headings_text = ' | '.join(content['headings'][:10])
            content_parts.append(f"HEADINGS: {headings_text}")
        
        # Main content (truncated for performance)
        if content['main_content']:
            main_truncated = content['main_content'][:2000]
            content_parts.append(f"CONTENT: {main_truncated}")
        
        # Hero section
        if content['hero_section']:
            hero_truncated = content['hero_section'][:1000]
            content_parts.append(f"HERO: {hero_truncated}")
        
        # Products (limited)
        if content['products']:
            products_text = ' | '.join(content['products'][:5])
            content_parts.append(f"PRODUCTS: {products_text}")
        
        # Business links (limited)
        if content['business_links']:
            links_text = ' | '.join([link['text'] for link in content['business_links'][:5]])
            content_parts.append(f"NAVIGATION: {links_text}")
        
        # Structured data (limited)
        if content['structured_data']:
            try:
                structured_text = json.dumps(content['structured_data'])[:500]
                content_parts.append(f"STRUCTURED: {structured_text}")
            except:
                pass
        
        final_text = ' || '.join(content_parts)
        
        # Final safety limit - never exceed 5000 characters
        if len(final_text) > 5000:
            final_text = final_text[:5000] + "..."
        
        return final_text
    
    async def scrape_website(self, url: str) -> ScrapedContent:
        """Optimized single-pass scraping with lxml parser"""
        try:
            session = await self._get_session()
            
            print(f"🎯 Starting optimized scrape of: {url}")
            
            # Fetch the webpage with retries
            html = await self._fetch_with_retries(session, url)
            
            # Use lxml parser for better performance
            soup = BeautifulSoup(html, 'lxml')
            
            print(f"📄 HTML content length: {len(html)} characters")
            
            # Remove noise elements early for better performance
            self._remove_noise_elements(soup)
            
            # Single-pass extraction of all content
            content = self._extract_all_content_single_pass(soup, url)
            
            # Generate focused raw text
            raw_text = self._generate_focused_raw_text(content)
            
            print(f"✅ Extracted {len(raw_text)} characters of focused business content")
            print(f"📊 Found: {len(content['headings'])} headings, {len(content['business_links'])} business links")
            
            return ScrapedContent(
                title=content['title'],
                meta_description=content['meta_description'],
                headings=content['headings'],
                main_content=content['main_content'],
                hero_section=content['hero_section'],
                products=content['products'],
                contact_info=content['contact_info'],
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
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()


# Global instance
scraper_runner = SimpleScraperRunner()