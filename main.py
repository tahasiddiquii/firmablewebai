"""
FirmableWebAI - Main FastAPI Application for Railway Deployment
AI-powered backend for extracting business insights from website homepages
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import sys
from typing import Optional, List, Dict, Any
import uvicorn
from pydantic import BaseModel, HttpUrl
from urllib.parse import urlparse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed. Run: pip install python-dotenv")
except Exception as e:
    print(f"⚠️ Could not load .env file: {e}")

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

# Import rate limiter
from app.rate_limiter import rate_limiter, get_rate_limiter

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
security = HTTPBearer(auto_error=False)  # auto_error=False for graceful handling

def get_api_secret_key() -> str:
    """Get API secret key from environment"""
    return os.getenv("API_SECRET_KEY", "demo-secret-key-for-development")

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify Bearer token authentication"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required. Use: Authorization: Bearer <your-api-key>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    expected_token = get_api_secret_key()
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key. Check your Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True

async def optional_verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Optional token verification for backward compatibility during migration"""
    if not credentials:
        # During migration phase, allow requests without auth
        print("⚠️ Request without authorization - migration mode")
        return False
    
    expected_token = get_api_secret_key()
    if credentials.credentials != expected_token:
        print("⚠️ Invalid token provided")
        return False
    
    print("✅ Valid token provided")
    return True


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
    # Initialize hybrid rate limiter (Redis with in-memory fallback)
    await rate_limiter.initialize()

@app.on_event("shutdown") 
async def shutdown():
    """Cleanup on shutdown"""
    await rate_limiter.close()

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


# Root endpoint - serve the Apple-style frontend
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serve Apple-style frontend HTML"""
    try:
        # Serve the frontend
        if os.path.exists("frontend/index.html"):
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

# Authentication test endpoint
@app.get("/api/auth/test",
        dependencies=[Depends(get_rate_limiter(times=30, seconds=60))])
async def test_auth(authenticated: bool = Depends(verify_token)):
    """Test authentication endpoint - requires Bearer token"""
    return {
        "message": "Authentication successful!",
        "authenticated": authenticated,
        "api_key_configured": bool(os.getenv("API_SECRET_KEY"))
    }

# Website Insights endpoint
@app.post("/api/insights", 
         response_model=InsightsResponse,
         dependencies=[Depends(get_rate_limiter(times=10, seconds=60))])
async def analyze_website(
    request: InsightsRequest,
    authenticated: bool = Depends(verify_token)
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
        
        # Validate response before creating Pydantic model
        validated_response = {
            "industry": response.get("industry") or "Business Services",
            "company_size": response.get("company_size"),
            "location": response.get("location"),
            "USP": response.get("USP"),
            "products": response.get("products") or [],
            "target_audience": response.get("target_audience"),
            "contact_info": response.get("contact_info") or {},
            "custom_answers": response.get("custom_answers")  # Include custom question answers
        }
        
        return InsightsResponse(**validated_response)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing insights request: {e}")
        import traceback
        traceback.print_exc()
        
        # Return a safe fallback response instead of 500 error
        fallback_response = {
            "industry": "Business Services",
            "company_size": None,
            "location": None,
            "USP": "Analysis temporarily unavailable",
            "products": [],
            "target_audience": None,
            "contact_info": {},
            "custom_answers": None
        }
        return InsightsResponse(**fallback_response)

# RAG Query endpoint
@app.post("/api/query", 
         response_model=QueryResponse,
         dependencies=[Depends(get_rate_limiter(times=20, seconds=60))])
async def query_website(
    request: QueryRequest,
    authenticated: bool = Depends(verify_token)
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
        
        # Double-check validation before proceeding
        print(f"🔍 Insights received in main: {insights}")
        
        # Ensure all required fields are properly set
        if not insights.get("industry") or insights.get("industry") == "":
            insights["industry"] = "Business Services"
            print(f"⚠️ Main validation: Fixed empty industry field")
        
        if not isinstance(insights.get("products"), list):
            insights["products"] = []
            print(f"⚠️ Main validation: Fixed products field")
        
        if not isinstance(insights.get("contact_info"), dict):
            insights["contact_info"] = {}
            print(f"⚠️ Main validation: Fixed contact_info field")
        
        print(f"✅ Generated AI insights successfully: {insights.get('industry')}")
        
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
                print("🔄 Creating text chunks for RAG...")
                chunks = llm_client.chunk_text(scraped_content.raw_text)
                print(f"✅ Created {len(chunks)} text chunks")
                
                embeddings = []
                print("🔄 Generating embeddings for chunks...")
                
                for i, chunk in enumerate(chunks):
                    print(f"   Generating embedding for chunk {i+1}/{len(chunks)}")
                    embedding = await llm_client.generate_embedding(chunk)
                    if embedding:
                        embeddings.append(embedding)
                        print(f"   ✅ Embedding {i+1}: {len(embedding)} dimensions")
                    else:
                        print(f"   ❌ Failed to generate embedding for chunk {i+1}")
                
                print(f"✅ Generated {len(embeddings)} embeddings out of {len(chunks)} chunks")
                
                # Save chunks to database
                if embeddings:
                    print("🔄 Saving chunks and embeddings to database...")
                    await postgres_client.save_chunks(website_id, chunks[:len(embeddings)], embeddings)
                    print("✅ Chunks and embeddings saved to database")
                else:
                    print("⚠️ No embeddings generated - skipping database save")
                
                chunks_created = len(embeddings)
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
        print(f"🔍 POSTGRES_URL configured: {bool(os.getenv('POSTGRES_URL'))}")
        
        # Try database-powered RAG first
        if os.getenv("POSTGRES_URL"):
            try:
                print("🔍 Using database RAG...")
                # Initialize database
                await postgres_client.initialize()
                print("✅ Database initialized")
                
                # Get website ID
                website_id = await postgres_client.get_or_create_website(url)
                print(f"✅ Website ID: {website_id}")
                
                # Check if website has been analyzed
                insights = await postgres_client.get_website_insights(website_id)
                print(f"✅ Insights found: {bool(insights)}")
                if not insights:
                    return {
                        "answer": "This website hasn't been analyzed yet. Please run the insights endpoint first to analyze the website content.",
                        "source_chunks": [],
                        "conversation_history": conversation_history
                    }
                
                # Generate embedding for the query
                print("🔄 Generating query embedding...")
                query_embedding = await llm_client.generate_embedding(query)
                print(f"✅ Query embedding generated: {len(query_embedding) if query_embedding else 0} dimensions")
                if not query_embedding:
                    raise Exception("Failed to generate query embedding")
                
                # Search for similar chunks
                print("🔄 Searching for similar chunks...")
                similar_chunks = await postgres_client.search_similar_chunks(
                    query_embedding, website_id, limit=5
                )
                print(f"✅ Found {len(similar_chunks)} similar chunks")
                
                if not similar_chunks:
                    return {
                        "answer": "I couldn't find relevant content to answer your question about this website.",
                        "source_chunks": [],
                        "conversation_history": conversation_history
                    }
                
                # Log chunks for debugging
                for i, chunk in enumerate(similar_chunks):
                    print(f"📄 Chunk {i+1}: {chunk[:100]}...")
                
                # Generate RAG response
                print("🔄 Generating RAG response...")
                answer = await llm_client.generate_rag_response(
                    query, similar_chunks, conversation_history
                )
                print(f"✅ RAG response generated: {len(answer)} characters")
                
                # Update conversation history
                updated_history = conversation_history.copy()
                updated_history.append({"role": "user", "content": query})
                updated_history.append({"role": "assistant", "content": answer})
                
                print("🎉 Full RAG response completed successfully!")
                return {
                    "answer": answer,
                    "source_chunks": similar_chunks,
                    "conversation_history": updated_history
                }
            except Exception as db_error:
                print(f"⚠️ Database RAG failed: {db_error}")
                import traceback
                traceback.print_exc()
        else:
            print("⚠️ No POSTGRES_URL configured, skipping database RAG")
        
        # Fallback: Simple AI response without RAG
        print("🤖 Using simple AI response (no RAG)...")
        
        # Generate a simple response using the LLM
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