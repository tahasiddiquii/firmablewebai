#!/usr/bin/env python3
"""
Test script for FirmableWebAI Railway deployment
Tests both local and deployed endpoints
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# Configuration
LOCAL_BASE_URL = "http://localhost:8000"
RAILWAY_BASE_URL = "https://your-railway-app.railway.app"  # Update with your actual Railway URL
DEMO_TOKEN = "demo-token-123"
TEST_URL = "https://openai.com"

def test_endpoint(base_url: str, endpoint: str, method: str = "GET", 
                 data: Dict[Any, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Test a single endpoint"""
    url = f"{base_url}{endpoint}"
    
    try:
        if method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=30)
        else:
            response = requests.get(url, headers=headers, timeout=30)
        
        return {
            "success": True,
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "url": url
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "url": url
        }

def run_tests(base_url: str, env_name: str):
    """Run all tests for a given environment"""
    print(f"\n🧪 Testing {env_name} Environment: {base_url}")
    print("=" * 60)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEMO_TOKEN}"
    }
    
    tests = [
        {
            "name": "Root Endpoint",
            "endpoint": "/",
            "method": "GET"
        },
        {
            "name": "Health Check",
            "endpoint": "/api/health",
            "method": "GET"
        },
        {
            "name": "Website Analysis",
            "endpoint": "/api/insights",
            "method": "POST",
            "data": {
                "url": TEST_URL,
                "questions": ["What industry is this company in?"]
            },
            "headers": headers
        },
        {
            "name": "RAG Query",
            "endpoint": "/api/query",
            "method": "POST", 
            "data": {
                "url": TEST_URL,
                "query": "What does this company do?",
                "conversation_history": []
            },
            "headers": headers
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n🔍 {test['name']}")
        print("-" * 40)
        
        result = test_endpoint(
            base_url=base_url,
            endpoint=test['endpoint'],
            method=test.get('method', 'GET'),
            data=test.get('data'),
            headers=test.get('headers')
        )
        
        results.append({**test, **result})
        
        if result['success']:
            print(f"✅ SUCCESS - Status: {result['status_code']}")
            if result['status_code'] == 200:
                response = result['response']
                if isinstance(response, dict):
                    # Pretty print key fields
                    if 'status' in response:
                        print(f"   Status: {response['status']}")
                    if 'service' in response:
                        print(f"   Service: {response['service']}")
                    if 'mode' in response:
                        print(f"   Mode: {response['mode']}")
                    if 'industry' in response:
                        print(f"   Industry: {response['industry']}")
                    if 'answer' in response:
                        print(f"   Answer: {response['answer'][:100]}...")
                    if 'message' in response:
                        print(f"   Message: {response['message']}")
                else:
                    print(f"   Response: {str(response)[:200]}...")
            else:
                print(f"   Response: {result['response']}")
        else:
            print(f"❌ FAILED - Error: {result['error']}")
    
    # Summary
    successful_tests = [r for r in results if r['success'] and r.get('status_code') == 200]
    print(f"\n📊 Summary for {env_name}:")
    print(f"   ✅ Successful: {len(successful_tests)}/{len(results)}")
    print(f"   ❌ Failed: {len(results) - len(successful_tests)}/{len(results)}")
    
    return results

def main():
    """Main test runner"""
    print("🚂 FirmableWebAI Railway Deployment Test Suite")
    print("=" * 60)
    
    # Test local development (optional)
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        print("\n🏠 Testing Local Development Server")
        print("Make sure you're running: python main.py")
        time.sleep(2)
        local_results = run_tests(LOCAL_BASE_URL, "Local Development")
    
    # Test deployed version
    if len(sys.argv) > 1 and sys.argv[1].startswith("https://"):
        deployed_url = sys.argv[1].rstrip('/')
        deployed_results = run_tests(deployed_url, "Deployed (Railway)")
    else:
        print(f"\n🌐 Testing Deployed Version")
        print("Update RAILWAY_BASE_URL in this script with your actual Railway URL")
        print("Or run: python test_railway.py https://your-app.railway.app")
        deployed_results = run_tests(RAILWAY_BASE_URL, "Deployed (Railway)")
    
    print(f"\n🎉 Testing Complete!")
    print("\n💡 Next Steps:")
    print("1. If demo mode works, add environment variables for live mode")
    print("2. Set OPENAI_API_KEY and POSTGRES_URL in Railway dashboard")
    print("3. Test again to verify live AI integration")
    print("4. Check Railway logs if any issues occur")

if __name__ == "__main__":
    main()
