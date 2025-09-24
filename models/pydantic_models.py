from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any


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
    custom_answers: Optional[Dict[str, str]] = None  # Answers to custom questions


class QueryRequest(BaseModel):
    url: HttpUrl
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = []


class QueryResponse(BaseModel):
    answer: str
    source_chunks: List[str]
    conversation_history: List[Dict[str, str]]


class ScrapedContent(BaseModel):
    title: Optional[str] = None
    meta_description: Optional[str] = None
    headings: List[str] = []
    main_content: Optional[str] = None
    hero_section: Optional[str] = None
    products: List[str] = []
    contact_info: Dict[str, Any] = {}
    raw_text: str = ""


class WebsiteChunk(BaseModel):
    id: Optional[int] = None
    website_id: int
    chunk_text: str
    embedding: Optional[List[float]] = None
