#!/usr/bin/env python3
"""
RAG Functionality Test Suite
Tests the Retrieval-Augmented Generation (RAG) system for conversational follow-up questions
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any

class RAGTester:
    """Comprehensive RAG functionality tester"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.conversation_history = []
        
    def test_insights_first(self, url: str) -> bool:
        """First analyze a website to populate the database for RAG"""
        print(f"1️⃣ ANALYZING WEBSITE: {url}")
        print("-" * 50)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/insights",
                json={"url": url},
                timeout=90
            )
            
            if response.status_code == 200:
                insights = response.json()
                print("✅ Website analysis successful!")
                print(f"📊 Industry: {insights.get('industry', 'N/A')}")
                print(f"📊 Company Size: {insights.get('company_size', 'N/A')}")
                print(f"📊 Products: {len(insights.get('products', []))} found")
                print(f"📊 USP: {insights.get('USP', 'N/A')[:100]}...")
                return True
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return False
    
    def test_rag_query(self, url: str, query: str, expected_keywords: List[str] = None) -> Dict[str, Any]:
        """Test a single RAG query"""
        print(f"\n❓ QUERY: {query}")
        print("-" * 30)
        
        try:
            payload = {
                "url": url,
                "query": query,
                "conversation_history": self.conversation_history
            }
            
            response = requests.post(
                f"{self.base_url}/api/query",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', '')
                source_chunks = result.get('source_chunks', [])
                
                print("✅ RAG query successful!")
                print(f"📝 Answer: {answer}")
                print(f"📚 Source chunks: {len(source_chunks)} found")
                
                if source_chunks:
                    print("📄 First chunk preview:")
                    print(f"   {source_chunks[0][:100]}...")
                
                # Update conversation history
                self.conversation_history = result.get('conversation_history', [])
                
                # Check for expected keywords if provided
                keyword_score = 0
                if expected_keywords:
                    found_keywords = []
                    for keyword in expected_keywords:
                        if keyword.lower() in answer.lower():
                            found_keywords.append(keyword)
                            keyword_score += 1
                    
                    print(f"🔍 Keywords found: {found_keywords} ({keyword_score}/{len(expected_keywords)})")
                
                return {
                    "success": True,
                    "answer": answer,
                    "source_chunks": len(source_chunks),
                    "keyword_score": keyword_score,
                    "total_keywords": len(expected_keywords) if expected_keywords else 0
                }
            else:
                print(f"❌ RAG query failed: {response.status_code}")
                print(f"Response: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ RAG query error: {e}")
            return {"success": False, "error": str(e)}
    
    def test_conversation_continuity(self, url: str) -> bool:
        """Test that conversation history is maintained across queries"""
        print(f"\n2️⃣ TESTING CONVERSATION CONTINUITY")
        print("=" * 50)
        
        # First query
        result1 = self.test_rag_query(
            url, 
            "What industry is this company in?",
            ["industry", "business", "sector"]
        )
        
        if not result1["success"]:
            return False
        
        time.sleep(2)  # Brief pause
        
        # Follow-up query that references previous context
        result2 = self.test_rag_query(
            url,
            "What makes them different from other companies in that industry?",
            ["different", "unique", "advantage"]
        )
        
        if not result2["success"]:
            return False
        
        # Check if conversation history is growing
        history_length = len(self.conversation_history)
        print(f"\n📜 Conversation history: {history_length} messages")
        
        if history_length >= 4:  # 2 queries + 2 responses
            print("✅ Conversation continuity working!")
            return True
        else:
            print("❌ Conversation history not being maintained")
            return False
    
    def test_rag_accuracy(self, url: str) -> Dict[str, Any]:
        """Test RAG accuracy with specific business questions"""
        print(f"\n3️⃣ TESTING RAG ACCURACY")
        print("=" * 50)
        
        test_queries = [
            {
                "query": "Who is the target audience for this company?",
                "keywords": ["audience", "customers", "users", "target"]
            },
            {
                "query": "What are the main products or services offered?",
                "keywords": ["products", "services", "offerings"]
            },
            {
                "query": "What is the company's unique selling proposition?",
                "keywords": ["unique", "advantage", "different", "value"]
            },
            {
                "query": "How can I contact this company?",
                "keywords": ["contact", "email", "phone", "reach"]
            }
        ]
        
        results = []
        total_score = 0
        total_possible = 0
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}/4:")
            result = self.test_rag_query(url, test["query"], test["keywords"])
            
            if result["success"]:
                score = result.get("keyword_score", 0)
                possible = result.get("total_keywords", 0)
                total_score += score
                total_possible += possible
                
                results.append({
                    "query": test["query"],
                    "success": True,
                    "score": score,
                    "possible": possible,
                    "accuracy": (score / possible * 100) if possible > 0 else 0
                })
            else:
                results.append({
                    "query": test["query"],
                    "success": False,
                    "error": result.get("error", "Unknown error")
                })
            
            time.sleep(1)  # Brief pause between queries
        
        overall_accuracy = (total_score / total_possible * 100) if total_possible > 0 else 0
        
        print(f"\n📊 RAG ACCURACY REPORT:")
        print(f"Total Score: {total_score}/{total_possible}")
        print(f"Overall Accuracy: {overall_accuracy:.1f}%")
        
        return {
            "results": results,
            "total_score": total_score,
            "total_possible": total_possible,
            "accuracy": overall_accuracy
        }
    
    def test_vector_search(self, url: str) -> bool:
        """Test that vector search is working by asking specific questions"""
        print(f"\n4️⃣ TESTING VECTOR SEARCH")
        print("=" * 50)
        
        # Ask a very specific question that should require vector search
        result = self.test_rag_query(
            url,
            "Tell me about the company's technology and approach",
            ["technology", "approach", "platform", "solution"]
        )
        
        if result["success"] and result["source_chunks"] > 0:
            print("✅ Vector search working - found relevant chunks!")
            return True
        else:
            print("❌ Vector search may not be working properly")
            return False

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test RAG functionality")
    parser.add_argument("--url", default="https://firmablewebai-production.up.railway.app", help="Base URL of the application")
    parser.add_argument("--website", default="https://spillmate.ai/", help="Website to analyze and query")
    
    args = parser.parse_args()
    
    print("🤖 RAG FUNCTIONALITY TEST SUITE")
    print("=" * 40)
    print("Testing Retrieval-Augmented Generation capabilities:")
    print("• Website analysis and database storage")
    print("• Conversational follow-up questions")
    print("• Vector similarity search")
    print("• Conversation history maintenance")
    print("• Answer accuracy and relevance")
    print()
    
    tester = RAGTester(args.url)
    
    # Test 1: Analyze website first
    if not tester.test_insights_first(args.website):
        print("❌ Website analysis failed - cannot test RAG")
        return False
    
    print("\n⏳ Waiting 10 seconds for database processing...")
    time.sleep(10)
    
    # Test 2: Conversation continuity
    if not tester.test_conversation_continuity(args.website):
        print("❌ Conversation continuity test failed")
        return False
    
    # Test 3: RAG accuracy
    accuracy_results = tester.test_rag_accuracy(args.website)
    
    # Test 4: Vector search
    vector_search_ok = tester.test_vector_search(args.website)
    
    # Final assessment
    print(f"\n🎯 FINAL RAG ASSESSMENT:")
    print("=" * 30)
    
    success_count = 0
    total_tests = 4
    
    print("✅ Website Analysis: PASS")
    success_count += 1
    
    if len(tester.conversation_history) >= 4:
        print("✅ Conversation Continuity: PASS")
        success_count += 1
    else:
        print("❌ Conversation Continuity: FAIL")
    
    if accuracy_results["accuracy"] >= 50:
        print(f"✅ RAG Accuracy: PASS ({accuracy_results['accuracy']:.1f}%)")
        success_count += 1
    else:
        print(f"❌ RAG Accuracy: FAIL ({accuracy_results['accuracy']:.1f}%)")
    
    if vector_search_ok:
        print("✅ Vector Search: PASS")
        success_count += 1
    else:
        print("❌ Vector Search: FAIL")
    
    overall_success = (success_count / total_tests) * 100
    print(f"\n📊 Overall RAG Score: {success_count}/{total_tests} ({overall_success:.0f}%)")
    
    if overall_success >= 75:
        print("🎉 RAG FUNCTIONALITY: EXCELLENT!")
        print("Your RAG system is working perfectly!")
    elif overall_success >= 50:
        print("⚠️ RAG FUNCTIONALITY: GOOD")
        print("RAG system is working but may need some improvements")
    else:
        print("❌ RAG FUNCTIONALITY: NEEDS WORK")
        print("RAG system has significant issues that need attention")
    
    return overall_success >= 50

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
