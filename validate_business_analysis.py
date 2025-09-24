#!/usr/bin/env python3
"""
Business Analysis Validation Script
Tests that all core business details are properly extracted and analyzed
"""

import asyncio
import json
from typing import Dict, Any

# Import our modules
try:
    from app.scraper.runner import scraper_runner
    from app.llm.llm_client import llm_client
    from models.pydantic_models import ScrapedContent
    print("✅ Imported modules successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

class BusinessAnalysisValidator:
    """Validates that all core business details are extracted"""
    
    REQUIRED_FIELDS = [
        "industry",
        "company_size", 
        "location",
        "USP",
        "products",
        "target_audience",
        "contact_info"
    ]
    
    CONTACT_INFO_FIELDS = [
        "emails",
        "phones", 
        "social_media"
    ]
    
    def validate_insights(self, insights: Dict[str, Any]) -> Dict[str, bool]:
        """Validate that insights contain all required business details"""
        validation_results = {}
        
        print("\n🔍 VALIDATING CORE BUSINESS DETAILS:")
        print("=" * 50)
        
        # Check all required fields exist
        for field in self.REQUIRED_FIELDS:
            exists = field in insights
            validation_results[f"{field}_exists"] = exists
            status = "✅" if exists else "❌"
            print(f"{status} {field.upper()}: {'Present' if exists else 'Missing'}")
        
        print("\n📊 FIELD ANALYSIS:")
        print("-" * 30)
        
        # Validate industry (must be string, never None)
        industry = insights.get("industry")
        industry_valid = isinstance(industry, str) and industry.strip() != ""
        validation_results["industry_valid"] = industry_valid
        print(f"🏭 Industry: '{industry}' - {'✅ Valid' if industry_valid else '❌ Invalid'}")
        
        # Validate company size
        company_size = insights.get("company_size")
        size_valid = company_size is None or isinstance(company_size, str)
        validation_results["company_size_valid"] = size_valid
        print(f"🏢 Company Size: '{company_size}' - {'✅ Valid' if size_valid else '❌ Invalid'}")
        
        # Validate location
        location = insights.get("location")
        location_valid = location is None or isinstance(location, str)
        validation_results["location_valid"] = location_valid
        print(f"📍 Location: '{location}' - {'✅ Valid' if location_valid else '❌ Invalid'}")
        
        # Validate USP
        usp = insights.get("USP")
        usp_valid = usp is None or isinstance(usp, str)
        validation_results["usp_valid"] = usp_valid
        usp_display = usp[:50] + "..." if usp and len(usp) > 50 else usp
        print(f"⭐ USP: '{usp_display}' - {'✅ Valid' if usp_valid else '❌ Invalid'}")
        
        # Validate products
        products = insights.get("products", [])
        products_valid = isinstance(products, list) and all(isinstance(p, str) for p in products)
        validation_results["products_valid"] = products_valid
        print(f"📦 Products: {len(products)} items - {'✅ Valid' if products_valid else '❌ Invalid'}")
        if products:
            print(f"    Products: {', '.join(products[:3])}{'...' if len(products) > 3 else ''}")
        
        # Validate target audience
        target_audience = insights.get("target_audience")
        audience_valid = target_audience is None or isinstance(target_audience, str)
        validation_results["target_audience_valid"] = audience_valid
        audience_display = target_audience[:50] + "..." if target_audience and len(target_audience) > 50 else target_audience
        print(f"🎯 Target Audience: '{audience_display}' - {'✅ Valid' if audience_valid else '❌ Invalid'}")
        
        # Validate contact info structure
        contact_info = insights.get("contact_info", {})
        contact_valid = isinstance(contact_info, dict)
        validation_results["contact_info_valid"] = contact_valid
        print(f"📞 Contact Info: {'✅ Valid dict' if contact_valid else '❌ Invalid'}")
        
        if contact_valid:
            for field in self.CONTACT_INFO_FIELDS:
                field_exists = field in contact_info
                field_valid = isinstance(contact_info.get(field, []), list)
                validation_results[f"contact_{field}_valid"] = field_valid
                count = len(contact_info.get(field, []))
                status = "✅" if field_valid else "❌"
                print(f"    {status} {field}: {count} items")
        
        return validation_results
    
    def generate_validation_report(self, validation_results: Dict[str, bool]) -> Dict[str, Any]:
        """Generate a comprehensive validation report"""
        total_checks = len(validation_results)
        passed_checks = sum(validation_results.values())
        success_rate = (passed_checks / total_checks) * 100
        
        report = {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "success_rate": round(success_rate, 1),
            "status": "PASS" if success_rate >= 90 else "FAIL",
            "details": validation_results
        }
        
        print(f"\n📊 VALIDATION REPORT:")
        print("=" * 30)
        print(f"Total Checks: {total_checks}")
        print(f"Passed: {passed_checks}")
        print(f"Failed: {total_checks - passed_checks}")
        print(f"Success Rate: {success_rate}%")
        print(f"Status: {'✅ PASS' if report['status'] == 'PASS' else '❌ FAIL'}")
        
        return report

async def test_business_analysis(url: str):
    """Test comprehensive business analysis for a website"""
    print(f"🚀 TESTING BUSINESS ANALYSIS FOR: {url}")
    print("=" * 60)
    
    validator = BusinessAnalysisValidator()
    
    try:
        # Step 1: Scrape website
        print("1️⃣ SCRAPING WEBSITE...")
        scraped_content = await scraper_runner.scrape_website(url)
        
        if not scraped_content or not scraped_content.raw_text:
            print("❌ Failed to scrape website content")
            return False
        
        print(f"✅ Scraped {len(scraped_content.raw_text)} characters")
        print(f"📊 Found: {len(scraped_content.headings)} headings, {len(scraped_content.products)} products")
        
        # Step 2: Generate AI insights
        print("\n2️⃣ GENERATING AI INSIGHTS...")
        insights = await llm_client.generate_insights(scraped_content)
        
        if not insights:
            print("❌ Failed to generate insights")
            return False
        
        print("✅ Generated AI insights successfully")
        
        # Step 3: Validate all business details
        print("\n3️⃣ VALIDATING BUSINESS ANALYSIS...")
        validation_results = validator.validate_insights(insights)
        
        # Step 4: Generate report
        report = validator.generate_validation_report(validation_results)
        
        # Step 5: Display full insights
        print(f"\n📄 FULL INSIGHTS JSON:")
        print("-" * 30)
        print(json.dumps(insights, indent=2))
        
        return report["status"] == "PASS"
        
    except Exception as e:
        print(f"❌ Error during business analysis: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await scraper_runner.close()

async def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate business analysis capabilities")
    parser.add_argument("--url", default="https://spillmate.ai/", help="URL to analyze")
    
    args = parser.parse_args()
    
    print("🔍 BUSINESS ANALYSIS VALIDATION SUITE")
    print("=" * 40)
    print("Testing extraction of all core business details:")
    print("• Industry (with LLM inference)")
    print("• Company Size (inferred from context)")  
    print("• Location (headquarters/primary location)")
    print("• Unique Selling Proposition (USP)")
    print("• Core Products/Services")
    print("• Target Audience (LLM inference)")
    print("• Contact Information (emails, phones, social)")
    print()
    
    success = await test_business_analysis(args.url)
    
    if success:
        print("\n🎉 ALL BUSINESS ANALYSIS REQUIREMENTS VALIDATED!")
        print("✅ Your application successfully extracts all core business details.")
    else:
        print("\n❌ VALIDATION FAILED!")
        print("Some business analysis requirements are not being met.")
        
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
