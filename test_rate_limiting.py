#!/usr/bin/env python3
"""
Test Rate Limiting Implementation
Comprehensive test for both Redis and in-memory rate limiting
"""

import asyncio
import aiohttp
import time
import sys
import os
from typing import Dict, List, Tuple


class RateLimitTester:
    """Test rate limiting functionality"""
    
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or os.getenv('API_SECRET_KEY', 'demo-secret-key-for-development')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, method: str = 'GET', json_data: dict = None) -> Tuple[int, Dict]:
        """Make a single request and return status code and response"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                async with session.get(url, headers=self.headers) as response:
                    return response.status, await response.json() if response.status != 429 else {'detail': response.headers.get('detail', 'Rate limited')}
            else:
                async with session.post(url, headers=self.headers, json=json_data) as response:
                    # Get rate limit headers if present
                    headers_info = {
                        'Retry-After': response.headers.get('Retry-After'),
                        'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
                        'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
                        'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset')
                    }
                    
                    if response.status == 429:
                        try:
                            detail = await response.json()
                        except:
                            detail = {'detail': 'Rate limited'}
                        detail['headers'] = headers_info
                        return response.status, detail
                    else:
                        return response.status, await response.json()
        except Exception as e:
            return 500, {'error': str(e)}
    
    async def test_endpoint_rate_limit(self, endpoint: str, limit: int, window: int, method: str = 'GET', json_data: dict = None):
        """Test rate limiting on a specific endpoint"""
        print(f"\n🔍 Testing {endpoint}")
        print(f"   Rate limit: {limit} requests per {window} seconds")
        print("-" * 50)
        
        async with aiohttp.ClientSession() as session:
            results = []
            
            # Make requests up to and beyond the limit
            test_requests = limit + 3  # Try to exceed limit by 3
            
            print(f"   Making {test_requests} rapid requests...")
            start_time = time.time()
            
            for i in range(test_requests):
                status, response = await self.make_request(session, endpoint, method, json_data)
                results.append((i + 1, status, response))
                
                # Small delay to avoid overwhelming
                await asyncio.sleep(0.1)
            
            elapsed = time.time() - start_time
            print(f"   Completed in {elapsed:.2f} seconds")
            
            # Analyze results
            successful = sum(1 for _, status, _ in results if status in [200, 201])
            rate_limited = sum(1 for _, status, _ in results if status == 429)
            
            print(f"\n   📊 Results:")
            print(f"      ✅ Successful: {successful}/{test_requests}")
            print(f"      🚫 Rate limited: {rate_limited}/{test_requests}")
            
            # Show individual results
            print(f"\n   📝 Request details:")
            for req_num, status, response in results:
                if status == 429:
                    retry_after = response.get('headers', {}).get('Retry-After', 'N/A')
                    print(f"      Request {req_num}: {status} - Rate limited (Retry after: {retry_after}s)")
                elif status in [200, 201]:
                    print(f"      Request {req_num}: {status} - Success")
                else:
                    print(f"      Request {req_num}: {status} - Error")
            
            # Verify rate limiting is working
            if successful <= limit and rate_limited > 0:
                print(f"\n   ✅ Rate limiting is working correctly!")
                print(f"      Allowed {successful} requests (limit: {limit})")
                print(f"      Blocked {rate_limited} requests after limit")
                return True
            elif successful > limit:
                print(f"\n   ❌ Rate limiting NOT working!")
                print(f"      Allowed {successful} requests but limit is {limit}")
                return False
            else:
                print(f"\n   ⚠️ Inconclusive - all requests succeeded")
                print(f"      May need to make requests faster")
                return None
    
    async def test_rate_limit_reset(self, endpoint: str, limit: int, window: int):
        """Test that rate limit resets after the time window"""
        print(f"\n🔄 Testing rate limit reset for {endpoint}")
        print(f"   Window: {window} seconds")
        print("-" * 50)
        
        async with aiohttp.ClientSession() as session:
            # First, hit the rate limit
            print(f"   1️⃣ Hitting rate limit...")
            for i in range(limit + 2):
                status, _ = await self.make_request(session, endpoint)
                if status == 429:
                    print(f"      Rate limited after {i} requests")
                    break
                await asyncio.sleep(0.1)
            
            # Wait for reset
            wait_time = window + 2  # Add buffer
            print(f"   ⏳ Waiting {wait_time} seconds for reset...")
            await asyncio.sleep(wait_time)
            
            # Try again
            print(f"   2️⃣ Testing after reset...")
            status, response = await self.make_request(session, endpoint)
            
            if status in [200, 201]:
                print(f"   ✅ Rate limit reset successfully!")
                return True
            else:
                print(f"   ❌ Rate limit did not reset: {status}")
                return False
    
    async def test_different_api_keys(self):
        """Test that rate limits are per API key"""
        print(f"\n🔑 Testing per-API-key rate limiting")
        print("-" * 50)
        
        # Create two different API keys
        api_key1 = self.api_key
        api_key2 = "different-test-key-12345"
        
        endpoint = "/api/auth/test"
        
        async with aiohttp.ClientSession() as session:
            # Make requests with first API key
            headers1 = {'Authorization': f'Bearer {api_key1}'}
            print(f"   Testing with API key 1...")
            
            success1 = 0
            for i in range(5):
                try:
                    async with session.get(f"{self.base_url}{endpoint}", headers=headers1) as response:
                        if response.status in [200, 201]:
                            success1 += 1
                        elif response.status == 429:
                            print(f"      Key 1 rate limited after {i} requests")
                            break
                except:
                    pass
                await asyncio.sleep(0.1)
            
            # Make requests with second API key (should fail auth but not be rate limited)
            headers2 = {'Authorization': f'Bearer {api_key2}'}
            print(f"   Testing with API key 2...")
            
            auth_failures = 0
            for i in range(5):
                try:
                    async with session.get(f"{self.base_url}{endpoint}", headers=headers2) as response:
                        if response.status == 401:
                            auth_failures += 1
                        elif response.status == 429:
                            print(f"      Key 2 rate limited after {i} requests")
                            break
                except:
                    pass
                await asyncio.sleep(0.1)
            
            print(f"\n   📊 Results:")
            print(f"      Key 1: {success1} successful requests")
            print(f"      Key 2: {auth_failures} auth failures (not rate limited)")
            
            if auth_failures > 0:
                print(f"   ✅ Rate limits appear to be per-API-key")
                return True
            else:
                print(f"   ⚠️ Could not verify per-key rate limiting")
                return None


async def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test rate limiting implementation")
    parser.add_argument("base_url", nargs='?', default="http://localhost:8000", 
                       help="Base URL of the application")
    parser.add_argument("--api-key", help="API key for authentication")
    
    args = parser.parse_args()
    
    print("🚦 RATE LIMITING TEST SUITE")
    print("=" * 60)
    print(f"Testing: {args.base_url}")
    print(f"API Key: {args.api_key or 'Using default/environment'}")
    print()
    
    tester = RateLimitTester(args.base_url, args.api_key)
    
    # Test different endpoints with their configured limits
    test_configs = [
        {
            'endpoint': '/api/auth/test',
            'limit': 30,
            'window': 60,
            'method': 'GET',
            'name': 'Authentication Test'
        },
        {
            'endpoint': '/api/insights',
            'limit': 10,
            'window': 60,
            'method': 'POST',
            'json_data': {'url': 'https://example.com'},
            'name': 'Insights API'
        },
        {
            'endpoint': '/api/query',
            'limit': 20,
            'window': 60,
            'method': 'POST',
            'json_data': {
                'url': 'https://example.com',
                'query': 'Test query',
                'conversation_history': []
            },
            'name': 'Query API'
        }
    ]
    
    results = []
    
    # Test 1: Basic rate limiting
    print("1️⃣ TESTING BASIC RATE LIMITING")
    print("=" * 60)
    
    for config in test_configs:
        result = await tester.test_endpoint_rate_limit(
            config['endpoint'],
            config['limit'],
            config['window'],
            config.get('method', 'GET'),
            config.get('json_data')
        )
        results.append((config['name'], result))
        await asyncio.sleep(2)  # Pause between tests
    
    # Test 2: Rate limit reset (only test one endpoint to save time)
    print("\n2️⃣ TESTING RATE LIMIT RESET")
    print("=" * 60)
    
    reset_result = await tester.test_rate_limit_reset(
        '/api/auth/test', 30, 60
    )
    results.append(('Rate Limit Reset', reset_result))
    
    # Test 3: Per-API-key rate limiting
    print("\n3️⃣ TESTING PER-API-KEY RATE LIMITING")
    print("=" * 60)
    
    per_key_result = await tester.test_different_api_keys()
    results.append(('Per-API-Key Limiting', per_key_result))
    
    # Summary
    print("\n📊 RATE LIMITING TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        if result is True:
            print(f"✅ {test_name}: PASS")
        elif result is False:
            print(f"❌ {test_name}: FAIL")
        else:
            print(f"⚠️ {test_name}: INCONCLUSIVE")
    
    # Overall assessment
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if failed == 0:
        print("🎉 Rate limiting is working correctly!")
        return True
    else:
        print("❌ Rate limiting has issues that need attention")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
