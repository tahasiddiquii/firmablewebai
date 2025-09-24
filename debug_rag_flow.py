#!/usr/bin/env python3
"""
Debug RAG Flow - Test complete flow from analysis to query
"""

import requests
import time
import json
import os

def test_complete_rag_flow(base_url: str, test_url: str):
    """Test complete RAG flow with debugging"""
    
    # Get API key for authentication
    api_key = os.getenv('API_SECRET_KEY', 'demo-secret-key-for-development')
    auth_headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"🔍 DEBUGGING COMPLETE RAG FLOW")
    print("=" * 50)
    print(f"Base URL: {base_url}")
    print(f"Test URL: {test_url}")
    print(f"🔑 API Key: {api_key[:20]}...")
    print()
    
    # Step 1: Analyze website to create embeddings
    print("1️⃣ ANALYZING WEBSITE TO CREATE EMBEDDINGS")
    print("-" * 40)
    
    try:
        response = requests.post(
            f"{base_url}/api/insights",
            json={"url": test_url},
            headers=auth_headers,
            timeout=120  # Longer timeout for analysis
        )
        
        if response.status_code == 200:
            insights = response.json()
            print("✅ Website analysis successful!")
            print(f"📊 Industry: {insights.get('industry', 'N/A')}")
            print(f"📊 Products: {len(insights.get('products', []))} found")
            print(f"📊 Contact Info: {insights.get('contact_info', {})}")
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return False
    
    # Step 2: Wait for processing
    print(f"\n⏳ Waiting 15 seconds for database processing...")
    time.sleep(15)
    
    # Step 3: Test RAG query
    print("\n2️⃣ TESTING RAG QUERY")
    print("-" * 40)
    
    queries = [
        "What industry is this company in?",
        "What products or services do they offer?",
        "Who is their target audience?",
        "How can I contact them?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        print("-" * 20)
        
        try:
            response = requests.post(
                f"{base_url}/api/query",
                json={
                    "url": test_url,
                    "query": query,
                    "conversation_history": []
                },
                headers=auth_headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', '')
                source_chunks = result.get('source_chunks', [])
                
                print(f"✅ Query successful!")
                print(f"📝 Answer: {answer[:200]}...")
                print(f"📚 Source chunks: {len(source_chunks)} found")
                
                if source_chunks:
                    print(f"📄 First chunk: {source_chunks[0][:100]}...")
                    
                    # Check if this is a real RAG response or fallback
                    if "Note: Full RAG capabilities will be available" in answer:
                        print("⚠️ FALLBACK: Using simple AI response (database not configured)")
                        return False
                    elif "Not available on the website" in answer and len(source_chunks) == 1 and "General knowledge" in source_chunks[0]:
                        print("⚠️ FALLBACK: Using general knowledge fallback")
                        return False
                    else:
                        print("✅ REAL RAG: Using database-backed response!")
                        return True
                else:
                    print("❌ No source chunks found - embeddings may not be stored")
                    
            else:
                print(f"❌ Query failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Query error: {e}")
            return False
        
        time.sleep(2)  # Brief pause between queries
    
    return False

def main():
    base_url = "https://firmablewebai-production.up.railway.app"
    test_url = "https://spillmate.ai/"
    
    print("🤖 RAG FLOW DEBUGGING TOOL")
    print("=" * 30)
    print("This tool will:")
    print("• Analyze a website to create embeddings")
    print("• Wait for database processing")
    print("• Test RAG queries to verify functionality")
    print("• Identify where the RAG flow breaks down")
    print()
    
    success = test_complete_rag_flow(base_url, test_url)
    
    if success:
        print("\n🎉 RAG FLOW WORKING!")
        print("✅ Embeddings are being stored and retrieved correctly")
        print("✅ Vector search is finding relevant content")
        print("✅ RAG responses are being generated from database")
    else:
        print("\n❌ RAG FLOW ISSUES DETECTED")
        print("The system is falling back to simple responses")
        print("Possible issues:")
        print("• Embeddings not being stored during analysis")
        print("• Database connection issues")
        print("• Vector search not finding chunks")
        print("• Chunk storage/retrieval problems")
        
        print("\n🔧 NEXT STEPS:")
        print("• Check Railway logs for detailed debugging output")
        print("• Verify database connection and pgvector setup")
        print("• Test embedding generation and storage")

if __name__ == "__main__":
    main()
