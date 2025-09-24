#!/usr/bin/env python3
"""
Test script for custom questions functionality in the insights endpoint.
This verifies that custom questions are properly answered and structured in the response.
"""

import requests
import json
import os
import sys
from typing import Dict, List, Optional

# Configuration
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')
API_KEY = os.getenv('API_SECRET_KEY', 'demo-secret-key-for-development')

def test_custom_questions(url: str, questions: List[str]) -> Dict:
    """Test the insights endpoint with custom questions."""
    
    endpoint = f"{BASE_URL}/api/insights"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "url": url,
        "questions": questions
    }
    
    print(f"🔍 Testing insights with custom questions:")
    print(f"   URL: {url}")
    print(f"   Questions:")
    for i, q in enumerate(questions, 1):
        print(f"      {i}. {q}")
    print()
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Request successful!")
            print("\n📊 Standard Insights:")
            print(f"   Industry: {data.get('industry')}")
            print(f"   Company Size: {data.get('company_size')}")
            print(f"   Location: {data.get('location')}")
            print(f"   USP: {data.get('USP')}")
            print(f"   Products: {data.get('products')}")
            print(f"   Target Audience: {data.get('target_audience')}")
            
            # Check for custom answers
            custom_answers = data.get('custom_answers')
            if custom_answers:
                print("\n🎯 Custom Question Answers:")
                for question, answer in custom_answers.items():
                    print(f"\n   Q: {question}")
                    print(f"   A: {answer}")
                return data
            else:
                print("\n⚠️  No custom answers found in response")
                return data
        else:
            print(f"❌ Request failed with status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
        return None

def run_tests():
    """Run various test scenarios for custom questions."""
    
    print("=" * 60)
    print("🧪 CUSTOM QUESTIONS FUNCTIONALITY TEST")
    print("=" * 60)
    print()
    
    # Test 1: Basic custom questions
    print("TEST 1: Basic Custom Questions")
    print("-" * 40)
    result1 = test_custom_questions(
        "https://www.tesla.com",
        [
            "What is the company's main product line?",
            "Does the company have any sustainability initiatives?",
            "What is their pricing strategy?"
        ]
    )
    print()
    
    # Test 2: Technical questions
    print("\nTEST 2: Technical Questions")
    print("-" * 40)
    result2 = test_custom_questions(
        "https://www.stripe.com",
        [
            "What programming languages does their API support?",
            "What security certifications do they have?",
            "How does their pricing model work?"
        ]
    )
    print()
    
    # Test 3: Business analysis questions
    print("\nTEST 3: Business Analysis Questions")
    print("-" * 40)
    result3 = test_custom_questions(
        "https://www.shopify.com",
        [
            "What is their competitive advantage?",
            "Who are their main competitors?",
            "What markets do they serve?",
            "Do they offer enterprise solutions?"
        ]
    )
    print()
    
    # Test 4: No custom questions (control test)
    print("\nTEST 4: No Custom Questions (Control)")
    print("-" * 40)
    result4 = test_custom_questions(
        "https://www.github.com",
        []
    )
    print()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 4
    
    # Check if custom answers were properly included
    if result1 and result1.get('custom_answers') and len(result1['custom_answers']) == 3:
        print("✅ Test 1: Custom answers included (3 questions)")
        tests_passed += 1
    else:
        print("❌ Test 1: Custom answers missing or incomplete")
    
    if result2 and result2.get('custom_answers') and len(result2['custom_answers']) == 3:
        print("✅ Test 2: Custom answers included (3 questions)")
        tests_passed += 1
    else:
        print("❌ Test 2: Custom answers missing or incomplete")
    
    if result3 and result3.get('custom_answers') and len(result3['custom_answers']) == 4:
        print("✅ Test 3: Custom answers included (4 questions)")
        tests_passed += 1
    else:
        print("❌ Test 3: Custom answers missing or incomplete")
    
    if result4 and (result4.get('custom_answers') is None or len(result4.get('custom_answers', {})) == 0):
        print("✅ Test 4: No custom answers when no questions provided")
        tests_passed += 1
    else:
        print("❌ Test 4: Unexpected custom answers field")
    
    print(f"\n📈 Results: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("\n🎉 All tests passed! Custom questions feature is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {tests_total - tests_passed} test(s) failed. Review the implementation.")
        return 1

if __name__ == "__main__":
    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=2)
        if health_response.status_code != 200:
            print("⚠️  Server health check failed. Is the server running?")
            print(f"   Try: python3 main.py")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server at", BASE_URL)
        print("   Please start the server first: python3 main.py")
        sys.exit(1)
    
    exit_code = run_tests()
    sys.exit(exit_code)
