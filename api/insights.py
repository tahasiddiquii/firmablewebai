from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio
from typing import Optional

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Try to import live components
try:
    from models.pydantic_models import InsightsRequest, InsightsResponse
    from app.scraper.runner import scraper_runner
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
            
            # Get URL from request
            url = data.get('url', '')
            questions = data.get('questions', [])
            
            if not url:
                self.send_error(400, 'URL is required')
                return
            
            if LIVE_MODE:
                # Live mode with real AI
                response = asyncio.run(self._process_live_request(url, questions))
            else:
                # Demo mode with mock data
                response = self._process_demo_request(url, questions)
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"Error processing request: {e}")
            error_response = {
                "industry": "Unknown",
                "company_size": None,
                "location": None,
                "USP": None,
                "products": [],
                "target_audience": None,
                "contact_info": {},
                "error": str(e),
                "mode": "error"
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    async def _process_live_request(self, url: str, questions: list):
        """Process request with real AI and database"""
        try:
            # Initialize database
            await postgres_client.initialize()
            await postgres_client.setup_schema()
            
            # Scrape website
            scraped_content = await scraper_runner.scrape_website(url)
            
            if not scraped_content.raw_text:
                raise Exception("Failed to scrape website content")
            
            # Generate insights
            insights = await llm_client.generate_insights(scraped_content, questions)
            
            # Save to database
            website_id = await postgres_client.get_or_create_website(url)
            await postgres_client.save_insights(website_id, insights)
            
            # Create chunks and embeddings for RAG
            chunks = llm_client.chunk_text(scraped_content.raw_text)
            embeddings = []
            
            for chunk in chunks:
                embedding = await llm_client.generate_embedding(chunk)
                if embedding:
                    embeddings.append(embedding)
            
            # Save chunks to database
            if embeddings:
                await postgres_client.save_chunks(website_id, chunks, embeddings)
            
            # Add mode indicator
            insights["mode"] = "live"
            insights["scraped_content_length"] = len(scraped_content.raw_text)
            insights["chunks_created"] = len(chunks)
            
            return insights
            
        except Exception as e:
            print(f"Live mode error: {e}")
            # Fallback to demo mode on error
            return self._process_demo_request(url, questions)
    
    def _process_demo_request(self, url: str, questions: list):
        """Process request with demo data"""
        # Extract domain for more realistic demo data
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        
        # Customize demo response based on domain
        if 'openai' in domain:
            return {
                "industry": "Artificial Intelligence",
                "company_size": "Large Enterprise",
                "location": "San Francisco, CA",
                "USP": "Leading AI research and deployment platform",
                "products": ["ChatGPT", "GPT-4", "OpenAI API", "DALL-E", "Codex"],
                "target_audience": "Developers, businesses, researchers",
                "contact_info": {
                    "emails": ["support@openai.com"],
                    "website": url
                },
                "mode": "demo",
                "note": "This is demo data. Enable live mode with environment variables."
            }
        elif 'google' in domain:
            return {
                "industry": "Technology",
                "company_size": "Large Enterprise",
                "location": "Mountain View, CA",
                "USP": "Search and cloud computing leader",
                "products": ["Google Search", "Google Cloud", "Gmail", "YouTube"],
                "target_audience": "Global consumers and businesses",
                "contact_info": {
                    "emails": ["support@google.com"],
                    "website": url
                },
                "mode": "demo",
                "note": "This is demo data. Enable live mode with environment variables."
            }
        else:
            return {
                "industry": "Technology",
                "company_size": "Medium Business",
                "location": "United States",
                "USP": "Innovative solutions for modern challenges",
                "products": ["Web Platform", "API Services", "Analytics Tools"],
                "target_audience": "Businesses and developers",
                "contact_info": {
                    "emails": ["contact@example.com"],
                    "website": url
                },
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
            "service": "website-insights",
            "mode": "live" if LIVE_MODE else "demo",
            "environment_variables": {
                "OPENAI_API_KEY": "✓" if os.getenv("OPENAI_API_KEY") else "✗",
                "POSTGRES_URL": "✓" if os.getenv("POSTGRES_URL") else "✗",
                "API_SECRET_KEY": "✓" if os.getenv("API_SECRET_KEY") else "✗ (using demo)"
            }
        }
        
        self.wfile.write(json.dumps(health_response).encode())
