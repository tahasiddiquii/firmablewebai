#!/usr/bin/env python3
"""
Test Authentication Implementation
Comprehensive test for Bearer token authentication
"""

import requests
import json
import os
import time

def test_authentication(base_url: str):
    """Test authentication implementation"""
    
    print("🔐 TESTING AUTHENTICATION IMPLEMENTATION")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print()
    
    # Test configuration
    valid_api_key = os.getenv('API_SECRET_KEY', 'demo-secret-key-for-development')
    invalid_api_key = 'invalid-key-12345'
    
    print(f"🔑 Valid API Key: {valid_api_key[:20]}...")
    print(f"❌ Invalid API Key: {invalid_api_key}")
    print()
    
    # Test 1: Public endpoints (should work without auth)
    print("1️⃣ TESTING PUBLIC ENDPOINTS (No Auth Required)")
    print("-" * 50)
    
    public_endpoints = [
        "/api/health",
        "/api/info",
        "/"
    ]
    
    for endpoint in public_endpoints:
        try:
            if endpoint == "/":
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            else:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ {endpoint}: Public access OK")
            else:
                print(f"   ❌ {endpoint}: Failed with status {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: Error - {e}")
    
    print()
    
    # Test 2: Auth test endpoint with valid token
    print("2️⃣ TESTING AUTH ENDPOINT - Valid Token")
    print("-" * 50)
    
    try:
        headers = {
            'Authorization': f'Bearer {valid_api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{base_url}/api/auth/test", headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Authentication successful!")
            print(f"   📊 Response: {json.dumps(result, indent=2)}")
        else:
            print(f"   ❌ Auth test failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Auth test error: {e}")
    
    print()
    
    # Test 3: Auth test endpoint with invalid token
    print("3️⃣ TESTING AUTH ENDPOINT - Invalid Token")
    print("-" * 50)
    
    try:
        headers = {
            'Authorization': f'Bearer {invalid_api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{base_url}/api/auth/test", headers=headers, timeout=10)
        
        if response.status_code == 401:
            print("   ✅ Correctly rejected invalid token (401)")
            error_response = response.json()
            print(f"   📄 Error message: {error_response.get('detail', 'No detail')}")
        else:
            print(f"   ❌ Expected 401, got {response.status_code}")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Invalid token test error: {e}")
    
    print()
    
    # Test 4: Auth test endpoint without token
    print("4️⃣ TESTING AUTH ENDPOINT - No Token")
    print("-" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/auth/test", timeout=10)
        
        if response.status_code == 401:
            print("   ✅ Correctly rejected missing token (401)")
            error_response = response.json()
            print(f"   📄 Error message: {error_response.get('detail', 'No detail')}")
        else:
            print(f"   ❌ Expected 401, got {response.status_code}")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ No token test error: {e}")
    
    print()
    
    # Test 5: Protected endpoints - Insights with valid token
    print("5️⃣ TESTING PROTECTED ENDPOINTS - Insights (Valid Token)")
    print("-" * 50)
    
    try:
        headers = {
            'Authorization': f'Bearer {valid_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {"url": "https://spillmate.ai"}
        response = requests.post(
            f"{base_url}/api/insights", 
            json=payload, 
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            insights = response.json()
            print("   ✅ Insights API with auth successful!")
            print(f"   📊 Industry: {insights.get('industry', 'N/A')}")
            print(f"   📊 Company Size: {insights.get('company_size', 'N/A')}")
        else:
            print(f"   ❌ Insights API failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Insights with auth error: {e}")
    
    print()
    
    # Test 6: Protected endpoints - Insights without token
    print("6️⃣ TESTING PROTECTED ENDPOINTS - Insights (No Token)")
    print("-" * 50)
    
    try:
        payload = {"url": "https://spillmate.ai"}
        response = requests.post(
            f"{base_url}/api/insights", 
            json=payload, 
            timeout=60
        )
        
        if response.status_code == 401:
            print("   ✅ Correctly rejected request without token (401)")
            error_response = response.json()
            print(f"   📄 Error message: {error_response.get('detail', 'No detail')}")
        else:
            print(f"   ❌ Expected 401, got {response.status_code}")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Insights without token error: {e}")
    
    print()
    
    # Test 7: Protected endpoints - Query with valid token
    print("7️⃣ TESTING PROTECTED ENDPOINTS - Query (Valid Token)")
    print("-" * 50)
    
    try:
        headers = {
            'Authorization': f'Bearer {valid_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "url": "https://spillmate.ai",
            "query": "What does this company do?",
            "conversation_history": []
        }
        response = requests.post(
            f"{base_url}/api/query", 
            json=payload, 
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Query API with auth successful!")
            print(f"   📊 Answer: {result.get('answer', 'N/A')[:100]}...")
        else:
            print(f"   ❌ Query API failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Query with auth error: {e}")
    
    print()
    
    # Summary
    print("🎯 AUTHENTICATION TEST SUMMARY")
    print("=" * 60)
    print("✅ Public endpoints should work without authentication")
    print("✅ Protected endpoints should require Bearer token")
    print("✅ Invalid/missing tokens should return 401 Unauthorized")
    print("✅ Valid tokens should allow access to protected endpoints")
    print()
    print("🚀 Authentication implementation complete!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        base_url = "http://localhost:8080"
    
    test_authentication(base_url)
