import os
import json
from typing import List, Dict, Any, Optional

# Import models with graceful fallback
try:
    from models.pydantic_models import ScrapedContent
except ImportError:
    ScrapedContent = None

# Import OpenAI with graceful fallback
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    AsyncOpenAI = None
    OPENAI_AVAILABLE = False


class LLMClient:
    def __init__(self):
        # Only initialize OpenAI client if API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and OPENAI_AVAILABLE:
            self.client = AsyncOpenAI(api_key=api_key)
            self.embedding_model = "text-embedding-3-large"
            self.available = True
        else:
            self.client = None
            self.embedding_model = None
            self.available = False
            print("LLMClient initialized without OpenAI API key - service unavailable")
    
    async def generate_insights(self, scraped_content: ScrapedContent, questions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate structured business insights using GPT-4.1"""
        
        if not self.available:
            raise Exception("OpenAI client not available - missing API key")
        
        # Prepare content for analysis
        content_text = f"""
        Title: {scraped_content.title or 'N/A'}
        Meta Description: {scraped_content.meta_description or 'N/A'}
        Headings: {', '.join(scraped_content.headings)}
        Main Content: {scraped_content.main_content or 'N/A'}
        Hero Section: {scraped_content.hero_section or 'N/A'}
        Products: {', '.join(scraped_content.products)}
        Contact Info: {scraped_content.contact_info}
        """
        
        questions_text = ""
        if questions:
            questions_text = f"\n\nAdditional Questions: {', '.join(questions)}"
        
        prompt = f"""You are an AI business analyst. Based on the following homepage text, extract structured insights:

Homepage Content: {content_text}{questions_text}

Output JSON with these exact keys and types:
- industry: string (required, never null)
- company_size: string or null
- location: string or null  
- USP: string or null
- products: array of strings (product names only, not objects)
- target_audience: string or null
- contact_info: object or empty object

IMPORTANT: 
- products must be an array of simple strings, not objects
- industry must always be a string, never null
- Return only valid JSON, no additional text or markdown formatting."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-1106-preview",  # GPT-4.1 equivalent
                messages=[
                    {"role": "system", "content": "You are a business analyst that extracts structured insights from website content. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean the content to extract just the JSON
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Parse JSON response
            insights = json.loads(content)
            print(f"🔍 Raw LLM response parsed: {insights}")
            
            # Validate and clean insights to ensure proper types
            products = insights.get("products") or []
            # Convert product objects to strings if needed
            if products and isinstance(products[0], dict):
                products = [prod.get("name", str(prod)) for prod in products if isinstance(prod, dict)]
            elif products and not all(isinstance(p, str) for p in products):
                products = [str(p) for p in products]
            
            # Ensure industry is never None or empty
            industry = insights.get("industry")
            if not industry or industry.strip() == "":
                industry = "Business Services"
                print(f"⚠️ Industry was None/empty, set to fallback: {industry}")
            
            cleaned_insights = {
                "industry": industry,
                "company_size": insights.get("company_size"),
                "location": insights.get("location"),
                "USP": insights.get("USP"),
                "products": products,
                "target_audience": insights.get("target_audience"),
                "contact_info": insights.get("contact_info") or {}
            }
            
            print(f"✅ Cleaned insights: {cleaned_insights}")
            return cleaned_insights
            
        except Exception as e:
            print(f"Error generating insights: {e}")
            print(f"Raw response content: {content if 'content' in locals() else 'No content received'}")
            return {
                "industry": "Business Services",
                "company_size": "Not specified",
                "location": "Not specified",
                "USP": "Not specified",
                "products": [],
                "target_audience": "Not specified",
                "contact_info": {}
            }
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using text-embedding-3-large"""
        
        if not self.available:
            return []
        
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
    
    async def generate_rag_response(self, query: str, retrieved_chunks: List[str], conversation_history: List[Dict[str, str]]) -> str:
        """Generate RAG response using GPT-4o-mini"""
        
        if not self.available:
            return "RAG response not available - OpenAI client not initialized"
        
        # Format conversation history
        history_text = ""
        if conversation_history:
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}" for msg in conversation_history
            ])
        
        # Format retrieved chunks
        chunks_text = "\n\n".join(retrieved_chunks)
        
        prompt = f"""You are an AI assistant answering questions based on retrieved website chunks.

Context Chunks:
{chunks_text}

Conversation History:
{history_text}

User Query: {query}

Provide a clear, grounded answer using only the information from the chunks.
If information is not available, respond with "Not available on the website."
Be conversational and helpful."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on website content. Be conversational and accurate."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating RAG response: {e}")
            return "I'm sorry, I encountered an error while processing your question. Please try again."
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks for embedding"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
            
            if start >= len(text):
                break
        
        return chunks


# Global instance
llm_client = LLMClient()
