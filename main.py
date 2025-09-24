"""
FirmableWebAI - Main FastAPI Application for Railway Deployment
AI-powered backend for extracting business insights from website homepages
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
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

# Initialize rate limiter
try:
    import redis
    from fastapi_limiter import FastAPILimiter
    from fastapi_limiter.depends import RateLimiter
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    print("Rate limiting not available - missing fastapi-limiter or redis")
    RATE_LIMITER_AVAILABLE = False
    RateLimiter = lambda *args, **kwargs: lambda func: func

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

# Mount static files for frontend assets
try:
    if os.path.exists("public"):
        app.mount("/static", StaticFiles(directory="public"), name="static")
    elif os.path.exists("frontend"):
        app.mount("/static", StaticFiles(directory="frontend"), name="static")
except Exception as e:
    print(f"Static files mounting failed: {e}")

@app.on_event("startup")
async def startup():
    """Initialize services on startup"""
    if RATE_LIMITER_AVAILABLE:
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            await FastAPILimiter.init(redis_client)
            print("✅ Rate limiter initialized")
        except Exception as e:
            print(f"⚠️ Rate limiter initialization failed: {e}")

@app.on_event("shutdown") 
async def shutdown():
    """Cleanup on shutdown"""
    if RATE_LIMITER_AVAILABLE:
        await FastAPILimiter.close()

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
    print(f"Critical import error - service unavailable: {e}")
    LIVE_MODE = False

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Bearer token"""
    expected_token = os.getenv("API_SECRET_KEY")
    if not expected_token:
        raise HTTPException(status_code=500, detail="API_SECRET_KEY environment variable not configured")
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.credentials

# Root endpoint - serve the Apple-style frontend
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serve Apple-style frontend HTML"""
    try:
        # Try to serve the new Apple-style frontend first
        if os.path.exists("frontend/apple-style.html"):
            with open("frontend/apple-style.html", "r") as f:
                return HTMLResponse(content=f.read())
        # Fallback to other frontend files
        elif os.path.exists("public/index.html"):
            with open("public/index.html", "r") as f:
                return HTMLResponse(content=f.read())
        elif os.path.exists("frontend/index.html"):
            with open("frontend/index.html", "r") as f:
                return HTMLResponse(content=f.read())
        else:
            # If no frontend files found, return API info
            return HTMLResponse(content="""
            <html>
                <body style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 40px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; min-height: 100vh;">
                    <h1>FirmableWebAI API</h1>
                    <p>Version: 1.0.0</p>
                    <p>Status: Healthy</p>
                    <p>Mode: """ + ("Live" if LIVE_MODE else "Demo") + """</p>
                    <p><a href="/docs" style="color: white;">Interactive API Documentation</a></p>
                    <p><a href="/api/health" style="color: white;">Health Check</a></p>
                </body>
            </html>
            """)
    except Exception as e:
        print(f"Error serving frontend: {e}")
        return HTMLResponse(content=f"<html><body style='font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 40px; text-align: center;'><h1>FirmableWebAI API</h1><p>Frontend loading error: {str(e)}</p><p><a href='/docs'>API Docs</a></p></body></html>")

# API info endpoint
@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "message": "FirmableWebAI API",
        "version": "1.0.0",
        "status": "healthy",
        "mode": "live" if LIVE_MODE else "unavailable",
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
        "status": "healthy" if LIVE_MODE else "degraded",
        "service": "firmablewebai",
        "mode": "live" if LIVE_MODE else "unavailable",
        "environment_variables": {
            "OPENAI_API_KEY": "✓" if os.getenv("OPENAI_API_KEY") else "✗",
            "POSTGRES_URL": "✓" if os.getenv("POSTGRES_URL") else "✗",
            "API_SECRET_KEY": "✓" if os.getenv("API_SECRET_KEY") else "✗"
        }
    }

# Website Insights endpoint
@app.post("/api/insights", response_model=InsightsResponse)
async def analyze_website(
    request: InsightsRequest,
    token: str = Depends(verify_token),
    ratelimit: dict = Depends(RateLimiter(times=10, seconds=60)) if RATE_LIMITER_AVAILABLE else None
):
    """
    Analyze a website and extract business insights.
    
    - **url**: Website URL to analyze
    - **questions**: Optional list of specific questions to answer
    """
    try:
        if not LIVE_MODE:
            raise HTTPException(status_code=503, detail="Service not available - OpenAI API key not configured")
        
        response = await process_live_insights(str(request.url), request.questions or [])
        return InsightsResponse(**response)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing insights request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze website: {str(e)}")

# RAG Query endpoint
@app.post("/api/query", response_model=QueryResponse)
async def query_website(
    request: QueryRequest,
    token: str = Depends(verify_token),
    ratelimit: dict = Depends(RateLimiter(times=20, seconds=60)) if RATE_LIMITER_AVAILABLE else None
):
    """
    Ask questions about a previously analyzed website using RAG.
    
    - **url**: Website URL that was previously analyzed
    - **query**: Question to ask about the website
    - **conversation_history**: Previous conversation context
    """
    try:
        if not LIVE_MODE:
            raise HTTPException(status_code=503, detail="Service not available - OpenAI API key not configured")
        
        response = await process_live_query(
            str(request.url), 
            request.query, 
            request.conversation_history
        )
        return QueryResponse(**response)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing query request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

# Live mode functions (only called if LIVE_MODE is True)
async def process_live_insights(url: str, questions: list):
    """Process insights request with real AI (database optional)"""
    try:
        print(f"🚀 Starting live analysis for: {url}")
        
        # Scrape website
        scraped_content = await scraper_runner.scrape_website(url)
        
        if not scraped_content or not scraped_content.raw_text:
            raise Exception("Failed to scrape website content")
        
        print(f"✅ Scraped {len(scraped_content.raw_text)} characters of content")
        
        # Generate insights using real AI
        insights = await llm_client.generate_insights(scraped_content, questions)
        
        print(f"✅ Generated AI insights successfully")
        
        # Try to save to database if available (optional)
        chunks_created = 0
        try:
            if os.getenv("POSTGRES_URL"):
                print("💾 Saving to database...")
                await postgres_client.initialize()
                await postgres_client.setup_schema()
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
                
                chunks_created = len(chunks)
                print(f"✅ Saved {chunks_created} chunks to database")
            else:
                print("⚠️ Database not configured, skipping storage (analysis still works!)")
        except Exception as db_error:
            print(f"⚠️ Database error (continuing without DB): {db_error}")
        
        # Add metadata
        insights["mode"] = "live"
        insights["scraped_content_length"] = len(scraped_content.raw_text)
        insights["chunks_created"] = chunks_created
        insights["database_enabled"] = bool(os.getenv("POSTGRES_URL"))
        
        print(f"🎉 Live analysis complete!")
        return insights
        
    except Exception as e:
        print(f"❌ Live mode error: {e}")
        raise Exception(f"Insights processing failed: {e}")

async def process_live_query(url: str, query: str, conversation_history: list):
    """Process query with real RAG system (database optional)"""
    try:
        print(f"💬 Processing query: {query}")
        
        # Try database-powered RAG first
        if os.getenv("POSTGRES_URL"):
            try:
                print("🔍 Using database RAG...")
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
            except Exception as db_error:
                print(f"⚠️ Database RAG failed: {db_error}")
        
        # Fallback: Simple AI response without RAG
        print("🤖 Using simple AI response (no RAG)...")
        
        # Generate a simple response using the LLM
        simple_prompt = f"Based on a website analysis for {url}, please answer this question: {query}"
        
        # Use the LLM to generate a response
        answer = await llm_client.generate_rag_response(
            query, [f"Website: {url}"], conversation_history
        )
        
        # Update conversation history
        updated_history = conversation_history.copy()
        updated_history.append({"role": "user", "content": query})
        updated_history.append({"role": "assistant", "content": answer})
        
        return {
            "answer": answer + "\n\n(Note: Full RAG capabilities will be available once database is configured)",
            "source_chunks": [f"General knowledge about {url}"],
            "conversation_history": updated_history
        }
        
    except Exception as e:
        print(f"❌ Live query error: {e}")
        raise Exception(f"Query processing failed: {e}")

# Startup logging - this will show in Railway logs
print(f"FirmableWebAI starting up...")
print(f"Live mode: {LIVE_MODE}")
print(f"Environment variables:")
print(f"  - OPENAI_API_KEY: {'✓' if os.getenv('OPENAI_API_KEY') else '✗'}")
print(f"  - POSTGRES_URL: {'✓' if os.getenv('POSTGRES_URL') else '✗'}")
print(f"  - API_SECRET_KEY: {'✓' if os.getenv('API_SECRET_KEY') else '✗'}")
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