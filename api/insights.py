from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict
import os
import sys
import asyncio

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from models.pydantic_models import InsightsRequest, InsightsResponse
    from app.scraper.runner import scraper_runner
    from app.llm.llm_client import llm_client
    from app.db.postgres_client import postgres_client
    LIVE_MODE = True
except ImportError:
    # Fallback for deployment without dependencies
    LIVE_MODE = False
    
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
        contact_info: Optional[Dict] = None

app = FastAPI(title="FirmableWebAI - Website Insights", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_token(authorization: Optional[str] = Header(None)):
    """Verify Bearer token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.split(" ")[1]
    expected_token = os.getenv("API_SECRET_KEY", "demo-token-123")
    
    if token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return token

@app.post("/", response_model=InsightsResponse)
async def get_website_insights(request: InsightsRequest, authorization: Optional[str] = Header(None)):
    """
    Scrape website homepage and generate structured business insights.
    
    - **url**: Website URL to analyze
    - **questions**: Optional list of specific questions to answer
    """
    # Verify token
    verify_token(authorization)
    
    try:
        if LIVE_MODE:
            # Real implementation with AI and database
            scraped_content = await scraper_runner.scrape_website(str(request.url))
            
            if not scraped_content.raw_text:
                raise HTTPException(status_code=400, detail="Failed to scrape website content")
            
            insights = await llm_client.generate_insights(scraped_content, request.questions)
            
            # Save to database
            await postgres_client.initialize()
            await postgres_client.setup_schema()
            website_id = await postgres_client.get_or_create_website(str(request.url))
            await postgres_client.save_insights(website_id, insights)
            
            # Create chunks and embeddings for RAG
            chunks = llm_client.chunk_text(scraped_content.raw_text)
            embeddings = []
            
            for chunk in chunks:
                embedding = await llm_client.generate_embedding(chunk)
                if embedding:
                    embeddings.append(embedding)
            
            if embeddings:
                await postgres_client.save_chunks(website_id, chunks, embeddings)
            
            return InsightsResponse(**insights)
        else:
            # Mock response for demo
            url = str(request.url)
            return InsightsResponse(
                industry="Technology",
                company_size="Large Enterprise",
                location="San Francisco, CA",
                USP="Leading AI research and deployment",
                products=["AI Platform", "API Services", "Machine Learning Tools"],
                target_audience="Developers, businesses, researchers",
                contact_info={
                    "emails": ["contact@example.com"],
                    "website": url
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "website-insights", "mode": "live" if LIVE_MODE else "demo"}

# Vercel handler
handler = app
