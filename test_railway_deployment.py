#!/usr/bin/env python3
"""
Test Railway deployment for FirmableWebAI
This script tests the deployed Railway app to ensure all fixes are working
"""

import requests
import json
import sys
import time

def test_railway_deployment(railway_url: str):
    """Test the Railway deployment"""
    
    # Remove trailing slash
    base_url = railway_url.rstrip('/')
    
    print(f"🚂 Testing Railway deployment: {base_url}")
    print("=" * 60)
    
    # Test 1: Health check
    print("1️⃣ Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health check passed")
            print(f"   📊 Status: {health_data.get('status', 'unknown')}")
            print(f"   📊 Mode: {health_data.get('mode', 'unknown')}")
            print(f"   📊 OpenAI Key: {health_data.get('environment_variables', {}).get('OPENAI_API_KEY', '❌')}")
            
            if health_data.get('mode') != 'live':
                print("   ⚠️  WARNING: App is not in live mode - check OpenAI API key")
                return False
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    print()
    
    # Test 2: Frontend access
    print("2️⃣ Testing frontend access...")
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("   ✅ Frontend accessible")
        else:
            print(f"   ❌ Frontend error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Frontend error: {e}")
    
    print()
    
    # Test 3: Insights API
    print("3️⃣ Testing insights API with spillmate.ai...")
    try:
        payload = {"url": "https://spillmate.ai/"}
        response = requests.post(
            f"{base_url}/api/insights", 
            json=payload, 
            timeout=60  # Give it time for scraping and AI processing
        )
        
        if response.status_code == 200:
            insights = response.json()
            print("   ✅ Insights API working!")
            print(f"   📊 Industry: {insights.get('industry', 'N/A')}")
            print(f"   📊 Company Size: {insights.get('company_size', 'N/A')}")
            print(f"   📊 Location: {insights.get('location', 'N/A')}")
            print(f"   📊 USP: {insights.get('USP', 'N/A')[:100]}...")
            print(f"   📊 Products: {len(insights.get('products', []))} found")
            print(f"   📊 Target Audience: {insights.get('target_audience', 'N/A')}")
            
            # Check if it's real AI data or fallback
            if insights.get('industry') == 'Unknown':
                print("   ⚠️  WARNING: Received fallback data - AI processing may have failed")
                return False
            else:
                print("   🎉 Real AI insights generated successfully!")
                return True
                
        elif response.status_code == 503:
            print("   ❌ Service unavailable - OpenAI API key not configured")
            print("   💡 Configure OPENAI_API_KEY in Railway dashboard")
            return False
        else:
            print(f"   ❌ Insights API error: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ⏰ Request timed out - this is normal for first request (cold start)")
        print("   💡 Try again in a minute - Railway apps have cold start delays")
        return False
    except Exception as e:
        print(f"   ❌ Insights API error: {e}")
        return False

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Railway deployment")
    parser.add_argument("--url", help="Railway app URL (e.g., https://your-app.railway.app)")
    parser.add_argument("--wait", type=int, default=0, help="Wait N seconds before testing (for deployment)")
    
    args = parser.parse_args()
    
    if not args.url:
        print("🚂 Railway Deployment Tester")
        print("=" * 30)
        print("Please provide your Railway app URL:")
        print("Example: python3 test_railway_deployment.py --url https://your-app.railway.app")
        print()
        print("To find your Railway URL:")
        print("1. Go to https://railway.app/dashboard")
        print("2. Select your FirmableWebAI project")
        print("3. Click on your deployment")
        print("4. Copy the URL from the 'Domains' section")
        return
    
    if args.wait > 0:
        print(f"⏳ Waiting {args.wait} seconds for deployment...")
        time.sleep(args.wait)
    
    success = test_railway_deployment(args.url)
    
    if success:
        print()
        print("🎉 All tests passed! Your Railway deployment is working correctly.")
        print("🌐 You can now use the web interface to analyze websites.")
        print(f"🔗 Frontend: {args.url}")
        print(f"🔗 API Docs: {args.url}/docs")
    else:
        print()
        print("❌ Some tests failed. Check the output above for details.")
        print("💡 Common fixes:")
        print("   - Configure OPENAI_API_KEY in Railway dashboard")
        print("   - Wait a few minutes for deployment to complete")
        print("   - Check Railway logs for errors")

if __name__ == "__main__":
    main()
