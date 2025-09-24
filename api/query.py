from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Try to import live components
try:
    from models.pydantic_models import QueryRequest, QueryResponse
    from app.llm.llm_client import llm_client
    from app.db.postgres_client import postgres_client
    LIVE_MODE = bool(os.getenv("OPENAI_API_KEY"))
except ImportError as e:
    print(f"Import error (falling back to demo mode): {e}")
    LIVE_MODE = False

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Handle CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Verify token
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                self.send_error(401, 'Invalid authorization format')
                return
            
            token = auth_header.split(' ')[1]
            expected_token = os.getenv("API_SECRET_KEY", "demo-token-123")
            
            if token != expected_token:
                self.send_error(401, 'Invalid token')
                return
            
            # Get request data
            url = data.get('url', '')
            query = data.get('query', '')
            conversation_history = data.get('conversation_history', [])
            
            if not url or not query:
                self.send_error(400, 'URL and query are required')
                return
            
            if LIVE_MODE:
                # Live mode with real AI
                response = asyncio.run(self._process_live_query(url, query, conversation_history))
            else:
                # Demo mode with mock data
                response = self._process_demo_query(url, query, conversation_history)
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"Error processing query: {e}")
            error_response = {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "source_chunks": [],
                "conversation_history": conversation_history,
                "mode": "error"
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    async def _process_live_query(self, url: str, query: str, conversation_history: list):
        """Process query with real RAG system"""
        try:
            # Initialize database
            await postgres_client.initialize()
            
            # Get website ID
            website_id = await postgres_client.get_or_create_website(url)
            
            # Check if website has been analyzed
            insights = await postgres_client.get_website_insights(website_id)
            if not insights:
                return {
                    "answer": "This website hasn't been analyzed yet. Please run the insights endpoint first to analyze the website content.",
                    "source_chunks": [],
                    "conversation_history": conversation_history,
                    "mode": "live",
                    "error": "website_not_analyzed"
                }
            
            # Generate embedding for the query
            query_embedding = await llm_client.generate_embedding(query)
            if not query_embedding:
                raise Exception("Failed to generate query embedding")
            
            # Search for similar chunks
            similar_chunks = await postgres_client.search_similar_chunks(
                query_embedding, website_id, limit=5
            )
            
            if not similar_chunks:
                return {
                    "answer": "I couldn't find relevant content to answer your question about this website.",
                    "source_chunks": [],
                    "conversation_history": conversation_history,
                    "mode": "live",
                    "error": "no_relevant_content"
                }
            
            # Generate RAG response
            answer = await llm_client.generate_rag_response(
                query, similar_chunks, conversation_history
            )
            
            # Update conversation history
            updated_history = conversation_history.copy()
            updated_history.append({"role": "user", "content": query})
            updated_history.append({"role": "assistant", "content": answer})
            
            return {
                "answer": answer,
                "source_chunks": similar_chunks,
                "conversation_history": updated_history,
                "mode": "live",
                "chunks_found": len(similar_chunks)
            }
            
        except Exception as e:
            print(f"Live query error: {e}")
            # Fallback to demo mode on error
            return self._process_demo_query(url, query, conversation_history)
    
    def _process_demo_query(self, url: str, query: str, conversation_history: list):
        """Process query with demo responses"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        
        # Generate contextual demo response
        if 'pricing' in query.lower() or 'cost' in query.lower():
            answer = f"Based on the website {url}, I can see they offer various pricing tiers. This is a demo response - in live mode, I would analyze the actual pricing page content to give you specific details."
        elif 'product' in query.lower() or 'service' in query.lower():
            answer = f"The website {url} offers several products and services. This is a demo response showing the RAG system functionality. In live mode, I would retrieve actual content chunks about their offerings."
        elif 'contact' in query.lower():
            answer = f"For contact information about {url}, this demo shows how I would normally extract and present contact details from the website content using the RAG system."
        else:
            answer = f"Based on the website {url}, I can help answer your question: '{query}'. This is a demo response showing that the RAG conversation system is working. In live mode, I would analyze the actual website content and provide contextual answers."
        
        # Update conversation history
        updated_history = conversation_history.copy()
        updated_history.append({"role": "user", "content": query})
        updated_history.append({"role": "assistant", "content": answer})
        
        return {
            "answer": answer,
            "source_chunks": [
                f"Demo content chunk 1 from {domain}",
                f"Demo product information from {domain}",
                f"Demo contact details from {domain} footer"
            ],
            "conversation_history": updated_history,
            "mode": "demo",
            "note": "This is demo data. Enable live mode with environment variables."
        }
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        # Health check endpoint
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        health_response = {
            "status": "healthy",
            "service": "website-query",
            "mode": "live" if LIVE_MODE else "demo",
            "environment_variables": {
                "OPENAI_API_KEY": "✓" if os.getenv("OPENAI_API_KEY") else "✗",
                "POSTGRES_URL": "✓" if os.getenv("POSTGRES_URL") else "✗",
                "API_SECRET_KEY": "✓" if os.getenv("API_SECRET_KEY") else "✗ (using demo)"
            }
        }
        
        self.wfile.write(json.dumps(health_response).encode())
