import asyncio
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerRunner
from twisted.internet import asyncioreactor
from twisted.internet.defer import inlineCallbacks
from typing import Dict, Any
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.scraper.homepage_spider import HomepageSpider
from models.pydantic_models import ScrapedContent


class ScraperRunner:
    def __init__(self):
        self.results = {}
    
    async def scrape_website(self, url: str) -> ScrapedContent:
        """Scrape a website and return structured content"""
        try:
            # Install asyncio reactor for Twisted
            asyncioreactor.install()
            
            # Create crawler process
            process = CrawlerProcess({
                'USER_AGENT': 'FirmableWebAI/1.0 (+https://firmablewebai.com)',
                'ROBOTSTXT_OBEY': False,
                'DOWNLOAD_DELAY': 1,
                'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
                'CONCURRENT_REQUESTS': 1,
                'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
                'AUTOTHROTTLE_ENABLED': True,
                'AUTOTHROTTLE_START_DELAY': 1,
                'AUTOTHROTTLE_MAX_DELAY': 10,
                'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
                'AUTOTHROTTLE_DEBUG': False,
                'COOKIES_ENABLED': False,
                'TELNETCONSOLE_ENABLED': False,
                'LOG_LEVEL': 'WARNING'
            })
            
            # Create spider instance
            spider = HomepageSpider(url=url)
            
            # Run the spider
            deferred = process.crawl(spider)
            process.start()
            
            # Wait for the spider to complete
            await deferred
            
            # Get results from spider
            if hasattr(spider, 'results') and spider.results:
                result = spider.results[0]  # Get first result
            else:
                # Fallback: create empty result
                result = {
                    'title': None,
                    'meta_description': None,
                    'headings': [],
                    'main_content': None,
                    'hero_section': None,
                    'products': [],
                    'contact_info': {},
                    'raw_text': ""
                }
            
            return ScrapedContent(**result)
            
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


# Alternative async runner using CrawlerRunner
class AsyncScraperRunner:
    def __init__(self):
        self.runner = None
    
    async def scrape_website(self, url: str) -> ScrapedContent:
        """Scrape a website using CrawlerRunner (alternative approach)"""
        try:
            # Install asyncio reactor
            asyncioreactor.install()
            
            # Create crawler runner
            runner = CrawlerRunner({
                'USER_AGENT': 'FirmableWebAI/1.0 (+https://firmablewebai.com)',
                'ROBOTSTXT_OBEY': False,
                'DOWNLOAD_DELAY': 1,
                'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
                'CONCURRENT_REQUESTS': 1,
                'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
                'AUTOTHROTTLE_ENABLED': True,
                'AUTOTHROTTLE_START_DELAY': 1,
                'AUTOTHROTTLE_MAX_DELAY': 10,
                'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
                'AUTOTHROTTLE_DEBUG': False,
                'COOKIES_ENABLED': False,
                'TELNETCONSOLE_ENABLED': False,
                'LOG_LEVEL': 'WARNING'
            })
            
            # Create spider and run
            spider = HomepageSpider(url=url)
            deferred = runner.crawl(spider)
            
            # Wait for completion
            result = await deferred
            
            # Extract results
            if hasattr(spider, 'results') and spider.results:
                scraped_data = spider.results[0]
            else:
                scraped_data = {
                    'title': None,
                    'meta_description': None,
                    'headings': [],
                    'main_content': None,
                    'hero_section': None,
                    'products': [],
                    'contact_info': {},
                    'raw_text': ""
                }
            
            return ScrapedContent(**scraped_data)
            
        except Exception as e:
            print(f"Error scraping website {url}: {e}")
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


# Global instance
scraper_runner = AsyncScraperRunner()
