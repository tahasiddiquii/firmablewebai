#!/usr/bin/env python3
"""
Test Mode for FirmableWebAI
This allows testing the application without an OpenAI API key
"""

import asyncio
import json
import sys
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

# Import our modules
try:
    from app.scraper.runner import scraper_runner
    from models.pydantic_models import ScrapedContent
    print("✅ Imported scraper successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class MockLLMClient:
    """Mock LLM client for testing without OpenAI API key"""
    
    def __init__(self):
        self.available = True
        print("🤖 Mock LLM Client initialized (Test Mode)")
    
    async def generate_insights(self, scraped_content: ScrapedContent, questions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate mock insights based on scraped content"""
        
        # Extract domain for industry guessing
        domain = scraped_content.title or "Unknown Website"
        raw_text = scraped_content.raw_text or ""
        
        # Simple heuristics for mock insights
        industry = self._guess_industry(domain, raw_text)
        company_size = self._guess_company_size(raw_text)
        location = self._extract_location(raw_text)
        usp = self._extract_usp(scraped_content)
        products = self._extract_products(scraped_content)
        target_audience = self._guess_target_audience(raw_text)
        contact_info = scraped_content.contact_info or {}
        
        insights = {
            "industry": industry,
            "company_size": company_size,
            "location": location,
            "USP": usp,
            "products": products,
            "target_audience": target_audience,
            "contact_info": contact_info,
            "test_mode": True,
            "scraped_content_length": len(raw_text)
        }
        
        print(f"🎭 Generated mock insights: {industry}")
        return insights
    
    def _guess_industry(self, title: str, content: str) -> str:
        """Simple industry classification based on keywords"""
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Technology keywords
        tech_keywords = ['ai', 'software', 'tech', 'app', 'platform', 'api', 'cloud', 'saas', 'digital']
        if any(keyword in title_lower or keyword in content_lower for keyword in tech_keywords):
            return "Technology"
        
        # E-commerce keywords
        ecommerce_keywords = ['shop', 'store', 'buy', 'sell', 'product', 'cart', 'checkout', 'payment']
        if any(keyword in title_lower or keyword in content_lower for keyword in ecommerce_keywords):
            return "E-commerce"
        
        # Healthcare keywords
        health_keywords = ['health', 'medical', 'doctor', 'clinic', 'hospital', 'care', 'treatment']
        if any(keyword in title_lower or keyword in content_lower for keyword in health_keywords):
            return "Healthcare"
        
        # Finance keywords
        finance_keywords = ['bank', 'finance', 'money', 'investment', 'loan', 'credit', 'financial']
        if any(keyword in title_lower or keyword in content_lower for keyword in finance_keywords):
            return "Financial Services"
        
        # Education keywords
        education_keywords = ['education', 'school', 'university', 'course', 'learn', 'training', 'academy']
        if any(keyword in title_lower or keyword in content_lower for keyword in education_keywords):
            return "Education"
        
        return "Business Services"
    
    def _guess_company_size(self, content: str) -> Optional[str]:
        """Guess company size based on content indicators"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['enterprise', 'corporation', 'global', 'worldwide', 'fortune']):
            return "Large (500+ employees)"
        elif any(word in content_lower for word in ['team', 'startup', 'founded', 'growing']):
            return "Small to Medium (10-500 employees)"
        elif any(word in content_lower for word in ['freelance', 'consultant', 'solo']):
            return "Small (1-10 employees)"
        
        return None
    
    def _extract_location(self, content: str) -> Optional[str]:
        """Extract location information from content"""
        # Simple location extraction (could be enhanced)
        import re
        
        # Look for common location patterns
        location_patterns = [
            r'\b(?:located in|based in|headquarters in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'\b([A-Z][a-z]+,\s*[A-Z]{2})\b',  # City, State
            r'\b([A-Z][a-z]+,\s*[A-Z][a-z]+)\b',  # City, Country
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, content)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_usp(self, scraped_content: ScrapedContent) -> Optional[str]:
        """Extract unique selling proposition from content"""
        # Use hero section or first heading as USP
        if scraped_content.hero_section:
            return scraped_content.hero_section[:200] + "..." if len(scraped_content.hero_section) > 200 else scraped_content.hero_section
        
        if scraped_content.headings:
            return scraped_content.headings[0]
        
        if scraped_content.meta_description:
            return scraped_content.meta_description
        
        return None
    
    def _extract_products(self, scraped_content: ScrapedContent) -> List[str]:
        """Extract products from scraped content"""
        return scraped_content.products[:5] if scraped_content.products else []
    
    def _guess_target_audience(self, content: str) -> Optional[str]:
        """Guess target audience based on content"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['business', 'enterprise', 'company', 'corporate']):
            return "Businesses and Enterprises"
        elif any(word in content_lower for word in ['developer', 'api', 'code', 'technical']):
            return "Developers and Technical Users"
        elif any(word in content_lower for word in ['consumer', 'personal', 'individual', 'family']):
            return "Individual Consumers"
        elif any(word in content_lower for word in ['professional', 'expert', 'specialist']):
            return "Professionals and Specialists"
        
        return "General Audience"

async def test_scraping(url: str):
    """Test website scraping"""
    print(f"🌐 Testing scraping for: {url}")
    
    try:
        scraped_content = await scraper_runner.scrape_website(url)
        
        print(f"✅ Scraping successful!")
        print(f"📊 Title: {scraped_content.title}")
        print(f"📊 Meta Description: {scraped_content.meta_description}")
        print(f"📊 Headings: {len(scraped_content.headings)}")
        print(f"📊 Products: {len(scraped_content.products)}")
        print(f"📊 Content Length: {len(scraped_content.raw_text)} characters")
        
        return scraped_content
        
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return None
    finally:
        await scraper_runner.close()

async def test_insights(scraped_content: ScrapedContent):
    """Test insights generation with mock LLM"""
    print(f"🤖 Testing insights generation...")
    
    mock_llm = MockLLMClient()
    insights = await mock_llm.generate_insights(scraped_content)
    
    print(f"✅ Insights generation successful!")
    print(f"📊 Industry: {insights['industry']}")
    print(f"📊 Company Size: {insights['company_size']}")
    print(f"📊 Location: {insights['location']}")
    print(f"📊 USP: {insights['USP']}")
    print(f"📊 Products: {insights['products']}")
    print(f"📊 Target Audience: {insights['target_audience']}")
    
    return insights

async def test_full_flow(url: str):
    """Test the complete flow"""
    print(f"🚀 Testing full flow for: {url}")
    print("=" * 50)
    
    # Step 1: Scrape website
    scraped_content = await test_scraping(url)
    if not scraped_content:
        return False
    
    print()
    
    # Step 2: Generate insights
    insights = await test_insights(scraped_content)
    if not insights:
        return False
    
    print()
    print("🎉 Full flow test completed successfully!")
    print("=" * 50)
    
    # Step 3: Display results in JSON format
    print("📄 Final Results (JSON):")
    print(json.dumps(insights, indent=2))
    
    return True

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test FirmableWebAI without OpenAI API key")
    parser.add_argument("--url", default="https://spillmate.ai/", help="URL to test")
    parser.add_argument("--scrape-only", action="store_true", help="Only test scraping")
    
    args = parser.parse_args()
    
    print("🧪 FirmableWebAI Test Mode")
    print("=" * 30)
    print("This mode allows testing without an OpenAI API key")
    print()
    
    if args.scrape_only:
        # Test scraping only
        asyncio.run(test_scraping(args.url))
    else:
        # Test full flow
        success = asyncio.run(test_full_flow(args.url))
        
        if success:
            print("\n✅ All tests passed! Your fixes are working correctly.")
            print("💡 To use with real AI, get an OpenAI API key and configure it in .env")
        else:
            print("\n❌ Some tests failed. Check the error messages above.")
            sys.exit(1)

if __name__ == "__main__":
    main()
