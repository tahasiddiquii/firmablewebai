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
            timeout = aiohttp.ClientTimeout(total=45)  # Increased timeout
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
    
    async def scrape_website(self, url: str) -> ScrapedContent:
        """Scrape a website comprehensively - capture EVERYTHING possible"""
        try:
            session = await self._get_session()
            
            print(f"🔍 Starting comprehensive scrape of: {url}")
            
            # Fetch the webpage with retries
            html = await self._fetch_with_retries(session, url)
            soup = BeautifulSoup(html, 'html.parser')
            
            print(f"📄 HTML content length: {len(html)} characters")
            
            # Extract ALL possible content
            title = self._extract_title(soup)
            meta_description = self._extract_meta_description(soup)
            all_meta_tags = self._extract_all_meta_tags(soup)
            headings = self._extract_headings(soup)
            main_content = self._extract_main_content(soup)
            hero_section = self._extract_hero_section(soup)
            products = self._extract_products(soup)
            contact_info = self._extract_contact_info(soup, html)
            
            # NEW: Extract everything else
            all_links = self._extract_all_links(soup, url)
            all_images = self._extract_all_images(soup, url)
            structured_data = self._extract_structured_data(soup)
            navigation_content = self._extract_navigation(soup)
            footer_content = self._extract_footer(soup)
            forms_content = self._extract_forms(soup)
            tables_content = self._extract_tables(soup)
            lists_content = self._extract_lists(soup)
            
            # Generate comprehensive raw text
            raw_text = self._extract_comprehensive_text(soup, {
                'meta_tags': all_meta_tags,
                'links': all_links,
                'images': all_images,
                'structured_data': structured_data,
                'navigation': navigation_content,
                'footer': footer_content,
                'forms': forms_content,
                'tables': tables_content,
                'lists': lists_content
            })
            
            print(f"✅ Extracted {len(raw_text)} characters of comprehensive content")
            print(f"📊 Found: {len(headings)} headings, {len(all_links)} links, {len(all_images)} images")
            
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
    
    # NEW COMPREHENSIVE EXTRACTION METHODS
    
    def _extract_all_meta_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract ALL meta tags"""
        meta_tags = {}
        for meta in soup.find_all('meta'):
            # Get name-based meta tags
            if meta.get('name'):
                meta_tags[f"meta_name_{meta.get('name')}"] = meta.get('content', '')
            # Get property-based meta tags (Open Graph, etc.)
            if meta.get('property'):
                meta_tags[f"meta_property_{meta.get('property')}"] = meta.get('content', '')
            # Get http-equiv meta tags
            if meta.get('http-equiv'):
                meta_tags[f"meta_http_equiv_{meta.get('http-equiv')}"] = meta.get('content', '')
        return meta_tags
    
    def _extract_all_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract ALL links with context"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = urljoin(base_url, href)
            
            link_text = link.get_text().strip()
            link_title = link.get('title', '')
            
            if link_text or link_title:  # Only include links with text
                links.append({
                    'url': href,
                    'text': link_text,
                    'title': link_title,
                    'context': self._get_element_context(link)
                })
        return links
    
    def _extract_all_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract ALL images with alt text and context"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src.startswith('/'):
                src = urljoin(base_url, src)
            
            alt_text = img.get('alt', '')
            title = img.get('title', '')
            
            images.append({
                'src': src,
                'alt': alt_text,
                'title': title,
                'context': self._get_element_context(img)
            })
        return images
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract JSON-LD and other structured data"""
        structured_data = {}
        
        # Extract JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                structured_data['json_ld'] = data
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # Extract microdata
        microdata_items = soup.find_all(attrs={'itemscope': True})
        if microdata_items:
            structured_data['microdata'] = []
            for item in microdata_items:
                item_type = item.get('itemtype', '')
                item_props = {}
                for prop in item.find_all(attrs={'itemprop': True}):
                    prop_name = prop.get('itemprop')
                    prop_value = prop.get('content') or prop.get_text().strip()
                    item_props[prop_name] = prop_value
                
                if item_props:
                    structured_data['microdata'].append({
                        'type': item_type,
                        'properties': item_props
                    })
        
        return structured_data
    
    def _extract_navigation(self, soup: BeautifulSoup) -> str:
        """Extract navigation content"""
        nav_content = []
        
        # Find navigation elements
        nav_selectors = ['nav', '.navigation', '.nav', '.menu', 'header nav', '.header-menu']
        
        for selector in nav_selectors:
            if selector.startswith('.'):
                elements = soup.select(selector)
            else:
                elements = soup.find_all(selector) if ' ' not in selector else soup.select(selector)
            
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) > 10:
                    nav_content.append(self._clean_text(text))
        
        return ' | '.join(nav_content)
    
    def _extract_footer(self, soup: BeautifulSoup) -> str:
        """Extract footer content"""
        footer_content = []
        
        footer_selectors = ['footer', '.footer', '.site-footer', '.page-footer']
        
        for selector in footer_selectors:
            if selector.startswith('.'):
                elements = soup.select(selector)
            else:
                elements = soup.find_all(selector)
            
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) > 20:
                    footer_content.append(self._clean_text(text))
        
        return ' | '.join(footer_content)
    
    def _extract_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract form information"""
        forms = []
        
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'get'),
                'fields': []
            }
            
            # Extract form fields
            for field in form.find_all(['input', 'select', 'textarea']):
                field_type = field.get('type', field.name)
                field_name = field.get('name', '')
                field_placeholder = field.get('placeholder', '')
                field_label = ''
                
                # Try to find associated label
                if field.get('id'):
                    label = form.find('label', {'for': field.get('id')})
                    if label:
                        field_label = label.get_text().strip()
                
                if field_name or field_placeholder or field_label:
                    form_data['fields'].append({
                        'type': field_type,
                        'name': field_name,
                        'placeholder': field_placeholder,
                        'label': field_label
                    })
            
            if form_data['fields']:
                forms.append(form_data)
        
        return forms
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[str]:
        """Extract table content"""
        tables = []
        
        for table in soup.find_all('table'):
            table_text = []
            
            # Extract headers
            headers = table.find_all('th')
            if headers:
                header_text = ' | '.join([th.get_text().strip() for th in headers])
                table_text.append(f"Headers: {header_text}")
            
            # Extract rows
            rows = table.find_all('tr')
            for row in rows[:5]:  # Limit to first 5 rows
                cells = row.find_all(['td', 'th'])
                if cells:
                    row_text = ' | '.join([cell.get_text().strip() for cell in cells])
                    if row_text:
                        table_text.append(row_text)
            
            if table_text:
                tables.append(' || '.join(table_text))
        
        return tables
    
    def _extract_lists(self, soup: BeautifulSoup) -> List[str]:
        """Extract list content"""
        lists = []
        
        for list_elem in soup.find_all(['ul', 'ol']):
            list_items = []
            for li in list_elem.find_all('li'):
                text = li.get_text().strip()
                if text and len(text) < 200:  # Reasonable list item length
                    list_items.append(text)
            
            if list_items and len(list_items) > 1:
                lists.append(' • '.join(list_items[:10]))  # Limit to 10 items
        
        return lists
    
    def _get_element_context(self, element) -> str:
        """Get context around an element"""
        context = []
        
        # Get parent element text (limited)
        parent = element.parent
        if parent and parent.name not in ['html', 'body']:
            parent_text = parent.get_text().strip()
            if len(parent_text) < 200:
                context.append(parent_text[:100])
        
        # Get sibling elements
        for sibling in element.find_next_siblings(limit=2):
            if sibling.name:
                sibling_text = sibling.get_text().strip()
                if sibling_text and len(sibling_text) < 100:
                    context.append(sibling_text[:50])
        
        return ' '.join(context)
    
    def _extract_comprehensive_text(self, soup: BeautifulSoup, extracted_data: Dict) -> str:
        """Generate comprehensive text from all extracted data"""
        content_parts = []
        
        # Start with basic page text (but don't remove scripts/styles yet)
        # We want to keep everything for LLM analysis
        page_text = soup.get_text()
        content_parts.append(f"PAGE_CONTENT: {self._clean_text(page_text)}")
        
        # Add meta tags information
        if extracted_data['meta_tags']:
            meta_text = ' '.join([f"{k}:{v}" for k, v in extracted_data['meta_tags'].items() if v])
            content_parts.append(f"META_TAGS: {meta_text}")
        
        # Add links information
        if extracted_data['links']:
            links_text = ' '.join([f"LINK({link['text']}:{link['url']})" for link in extracted_data['links'][:20] if link['text']])
            content_parts.append(f"LINKS: {links_text}")
        
        # Add images information
        if extracted_data['images']:
            images_text = ' '.join([f"IMAGE({img['alt']})" for img in extracted_data['images'][:10] if img['alt']])
            if images_text:
                content_parts.append(f"IMAGES: {images_text}")
        
        # Add structured data
        if extracted_data['structured_data']:
            try:
                structured_text = json.dumps(extracted_data['structured_data'])[:1000]  # Limit size
                content_parts.append(f"STRUCTURED_DATA: {structured_text}")
            except:
                pass
        
        # Add navigation
        if extracted_data['navigation']:
            content_parts.append(f"NAVIGATION: {extracted_data['navigation']}")
        
        # Add footer
        if extracted_data['footer']:
            content_parts.append(f"FOOTER: {extracted_data['footer']}")
        
        # Add forms
        if extracted_data['forms']:
            forms_text = ' '.join([f"FORM({form['method']}:{','.join([f['name'] for f in form['fields'] if f['name']])})" for form in extracted_data['forms']])
            content_parts.append(f"FORMS: {forms_text}")
        
        # Add tables
        if extracted_data['tables']:
            tables_text = ' '.join(extracted_data['tables'][:3])  # Limit to 3 tables
            content_parts.append(f"TABLES: {tables_text}")
        
        # Add lists
        if extracted_data['lists']:
            lists_text = ' '.join(extracted_data['lists'][:5])  # Limit to 5 lists
            content_parts.append(f"LISTS: {lists_text}")
        
        return ' || '.join(content_parts)
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()


# Global instance
scraper_runner = SimpleScraperRunner()
