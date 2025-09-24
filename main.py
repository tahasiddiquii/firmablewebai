"""
FirmableWebAI - Main FastAPI Application for Railway Deployment
AI-powered backend for extracting business insights from website homepages
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
import os
import sys
from typing import Optional, List, Dict, Any
import uvicorn
from pydantic import BaseModel, HttpUrl
from urllib.parse import urlparse

# Add the project root to the path
sys.path.append(os.path.dirname(__file__))

# Initialize FastAPI app first
app = FastAPI(
    title="FirmableWebAI",
    description="AI-powered backend for extracting business insights from website homepages with RAG-based conversational follow-up",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Pydantic models
class InsightsRequest(BaseModel):
    url: HttpUrl
    questions: Optional[List[str]] = None

class InsightsResponse(BaseModel):
    industry: str
    company_size: Optional[str] = None
    location: Optional[str] = None
    USP: Optional[str] = None
    products: Optional[List[str]] = None
    target_audience: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None

class QueryRequest(BaseModel):
    url: HttpUrl
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = []

class QueryResponse(BaseModel):
    answer: str
    source_chunks: List[str]
    conversation_history: List[Dict[str, str]]

# Try to import live components (graceful fallback)
LIVE_MODE = False
try:
    from app.scraper.runner import scraper_runner
    from app.llm.llm_client import llm_client
    from app.db.postgres_client import postgres_client
    LIVE_MODE = bool(os.getenv("OPENAI_API_KEY"))
    print(f"Live components imported successfully. Live mode: {LIVE_MODE}")
except ImportError as e:
    print(f"Import error (running in demo mode): {e}")
    LIVE_MODE = False

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Bearer token"""
    expected_token = os.getenv("API_SECRET_KEY", "demo-token-123")
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.credentials

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - serve frontend or API info"""
    return {
        "message": "FirmableWebAI API",
        "version": "1.0.0",
        "status": "healthy",
        "mode": "live" if LIVE_MODE else "demo",
        "docs": "/docs",
        "endpoints": {
            "insights": "/api/insights",
            "query": "/api/query",
            "health": "/api/health"
        }
    }

# Health check endpoint
@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "firmablewebai",
        "mode": "live" if LIVE_MODE else "demo",
        "environment_variables": {
            "OPENAI_API_KEY": "✓" if os.getenv("OPENAI_API_KEY") else "✗",
            "POSTGRES_URL": "✓" if os.getenv("POSTGRES_URL") else "✗",
            "API_SECRET_KEY": "✓" if os.getenv("API_SECRET_KEY") else "✗ (using demo)"
        }
    }

# Website Insights endpoint
@app.post("/api/insights", response_model=InsightsResponse)
async def analyze_website(
    request: InsightsRequest,
    token: str = Depends(verify_token)
):
    """
    Analyze a website and extract business insights.
    
    - **url**: Website URL to analyze
    - **questions**: Optional list of specific questions to answer
    """
    try:
        if LIVE_MODE:
            response = await process_live_insights(str(request.url), request.questions or [])
        else:
            response = process_demo_insights(str(request.url), request.questions or [])
        
        return InsightsResponse(**response)
        
    except Exception as e:
        print(f"Error processing insights request: {e}")
        # Return error response in expected format
        return InsightsResponse(
            industry="Unknown",
            company_size=None,
            location=None,
            USP=None,
            products=[],
            target_audience=None,
            contact_info={"error": str(e)}
        )

# RAG Query endpoint
@app.post("/api/query", response_model=QueryResponse)
async def query_website(
    request: QueryRequest,
    token: str = Depends(verify_token)
):
    """
    Ask questions about a previously analyzed website using RAG.
    
    - **url**: Website URL that was previously analyzed
    - **query**: Question to ask about the website
    - **conversation_history**: Previous conversation context
    """
    try:
        if LIVE_MODE:
            response = await process_live_query(
                str(request.url), 
                request.query, 
                request.conversation_history
            )
        else:
            response = process_demo_query(
                str(request.url), 
                request.query, 
                request.conversation_history
            )
        
        return QueryResponse(**response)
        
    except Exception as e:
        print(f"Error processing query request: {e}")
        return QueryResponse(
            answer=f"Sorry, I encountered an error: {str(e)}",
            source_chunks=[],
            conversation_history=request.conversation_history
        )

# Live mode functions (only called if LIVE_MODE is True)
async def process_live_insights(url: str, questions: list):
    """Process insights request with real AI and database"""
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
        
        # Add metadata
        insights["mode"] = "live"
        insights["scraped_content_length"] = len(scraped_content.raw_text)
        insights["chunks_created"] = len(chunks)
        
        return insights
        
    except Exception as e:
        print(f"Live mode error: {e}")
        # Fallback to demo mode on error
        return process_demo_insights(url, questions)

async def process_live_query(url: str, query: str, conversation_history: list):
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
                "conversation_history": conversation_history
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
                "conversation_history": conversation_history
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
            "conversation_history": updated_history
        }
        
    except Exception as e:
        print(f"Live query error: {e}")
        # Fallback to demo mode on error
        return process_demo_query(url, query, conversation_history)

# Demo mode functions
def process_demo_insights(url: str, questions: list):
    """Process request with demo data"""
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
            }
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
            }
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
            }
        }

def process_demo_query(url: str, query: str, conversation_history: list):
    """Process query with demo responses"""
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
        "conversation_history": updated_history
    }

# Startup logging - this will show in Railway logs
print(f"FirmableWebAI starting up...")
print(f"Live mode: {LIVE_MODE}")
print(f"Environment variables:")
print(f"  - OPENAI_API_KEY: {'✓' if os.getenv('OPENAI_API_KEY') else '✗'}")
print(f"  - POSTGRES_URL: {'✓' if os.getenv('POSTGRES_URL') else '✗'}")
print(f"  - API_SECRET_KEY: {'✓' if os.getenv('API_SECRET_KEY') else '✗ (using demo)'}")
print(f"  - PORT: {os.getenv('PORT', 'not set')}")

# Railway deployment entry point (only for local testing)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting FirmableWebAI locally on port {port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True
    )