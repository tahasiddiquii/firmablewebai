#!/usr/bin/env python3
"""
Debug location extraction - Check what content is being scraped
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(__file__))

from app.scraper.runner import scraper_runner

async def debug_location_extraction(url: str):
    """Debug location extraction from a website"""
    
    print(f"🔍 DEBUGGING LOCATION EXTRACTION")
    print("=" * 50)
    print(f"URL: {url}")
    print()
    
    try:
        # Scrape the website
        print("📄 SCRAPING WEBSITE...")
        scraped_content = await scraper_runner.scrape_website(url)
        
        print(f"✅ Title: {scraped_content.title}")
        print(f"✅ Meta Description: {scraped_content.meta_description}")
        print()
        
        # Check contact info for addresses
        print("📍 CONTACT INFO EXTRACTED:")
        contact_info = scraped_content.contact_info
        print(f"Contact Info: {contact_info}")
        
        if 'addresses' in contact_info:
            print(f"🏠 Addresses found: {contact_info['addresses']}")
        else:
            print("❌ No addresses found in contact info")
        
        print()
        
        # Check raw text for location keywords
        print("🔍 SEARCHING RAW TEXT FOR LOCATION KEYWORDS...")
        raw_text = scraped_content.raw_text.lower()
        
        location_keywords = [
            'based in', 'located in', 'headquartered', 'headquarters',
            'address:', 'location:', 'city', 'state', 'country',
            'san francisco', 'new york', 'london', 'california', 'ca',
            'usa', 'united states', 'uk', 'united kingdom'
        ]
        
        found_locations = []
        for keyword in location_keywords:
            if keyword in raw_text:
                # Find context around the keyword
                start = max(0, raw_text.find(keyword) - 50)
                end = min(len(raw_text), raw_text.find(keyword) + 100)
                context = raw_text[start:end].strip()
                found_locations.append(f"'{keyword}': ...{context}...")
        
        if found_locations:
            print("🎯 LOCATION KEYWORDS FOUND:")
            for location in found_locations[:5]:  # Show first 5
                print(f"   {location}")
        else:
            print("❌ No location keywords found in raw text")
        
        print()
        
        # Check specific sections
        print("📝 CHECKING SPECIFIC SECTIONS...")
        
        if scraped_content.headings:
            print(f"🔤 Headings: {scraped_content.headings[:5]}")  # First 5
        
        if scraped_content.hero_section:
            print(f"🦸 Hero Section (first 200 chars): {scraped_content.hero_section[:200]}...")
        
        if scraped_content.main_content:
            print(f"📄 Main Content (first 200 chars): {scraped_content.main_content[:200]}...")
        
        print()
        
        # Show raw text sample
        print("📜 RAW TEXT SAMPLE (first 500 characters):")
        print(f"{scraped_content.raw_text[:500]}...")
        
        print()
        print("🔍 ANALYSIS COMPLETE!")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper_runner.close()

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://spillmate.ai"
    asyncio.run(debug_location_extraction(url))
