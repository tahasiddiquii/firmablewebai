from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict
import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from models.pydantic_models import QueryRequest, QueryResponse
    from app.llm.llm_client import llm_client
    from app.db.postgres_client import postgres_client
    LIVE_MODE = True
except ImportError:
    # Fallback for deployment without dependencies
    LIVE_MODE = False
    
    class QueryRequest(BaseModel):
        url: HttpUrl
        query: str
        conversation_history: Optional[List[Dict[str, str]]] = []
    
    class QueryResponse(BaseModel):
        answer: str
        source_chunks: List[str]
        conversation_history: List[Dict[str, str]]

app = FastAPI(title="FirmableWebAI - Website Query", version="1.0.0")

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

@app.post("/", response_model=QueryResponse)
async def query_website(request: QueryRequest, authorization: Optional[str] = Header(None)):
    """
    Query website content using RAG (Retrieval-Augmented Generation).
    
    - **url**: Website URL to query
    - **query**: User question about the website
    - **conversation_history**: Previous conversation context
    """
    # Verify token
    verify_token(authorization)
    
    try:
        if LIVE_MODE:
            # Real implementation with AI and database
            await postgres_client.initialize()
            website_id = await postgres_client.get_or_create_website(str(request.url))
            
            # Check if website has been analyzed
            insights = await postgres_client.get_website_insights(website_id)
            if not insights:
                raise HTTPException(
                    status_code=404, 
                    detail="Website not analyzed. Please run /api/insights first."
                )
            
            # Generate embedding for the query
            query_embedding = await llm_client.generate_embedding(request.query)
            if not query_embedding:
                raise HTTPException(status_code=500, detail="Failed to generate query embedding")
            
            # Search for similar chunks
            similar_chunks = await postgres_client.search_similar_chunks(
                query_embedding, website_id, limit=5
            )
            
            if not similar_chunks:
                raise HTTPException(
                    status_code=404, 
                    detail="No relevant content found for this query"
                )
            
            # Generate RAG response
            answer = await llm_client.generate_rag_response(
                request.query, similar_chunks, request.conversation_history
            )
            
            # Update conversation history
            updated_history = request.conversation_history.copy()
            updated_history.append({"role": "user", "content": request.query})
            updated_history.append({"role": "assistant", "content": answer})
            
            return QueryResponse(
                answer=answer,
                source_chunks=similar_chunks,
                conversation_history=updated_history
            )
        else:
            # Mock response for demo
            url = str(request.url)
            query = request.query
            conversation_history = request.conversation_history
            
            answer = f"Based on the website {url}, I can help answer your question: '{query}'. This is a demo response showing that the RAG system is working. The system would normally analyze the website content and provide contextual answers."
            
            # Update conversation history
            updated_history = conversation_history.copy()
            updated_history.append({"role": "user", "content": query})
            updated_history.append({"role": "assistant", "content": answer})
            
            return QueryResponse(
                answer=answer,
                source_chunks=[
                    "Homepage content chunk 1 from the website",
                    "Product information from the about section", 
                    "Contact details from the footer"
                ],
                conversation_history=updated_history
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "website-query", "mode": "live" if LIVE_MODE else "demo"}

# Vercel handler
handler = app
