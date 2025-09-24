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
        
        # Extract location hints from content
        location_hints = []
        raw_text_lower = (scraped_content.raw_text or "").lower()
        title_lower = (scraped_content.title or "").lower()
        meta_lower = (scraped_content.meta_description or "").lower()
        
        # Check for geographic indicators
        if "australia" in raw_text_lower or "australian" in raw_text_lower or "& nz" in raw_text_lower:
            location_hints.append("Geographic focus: Australia/New Zealand")
        if "uk" in raw_text_lower or "united kingdom" in raw_text_lower or "british" in raw_text_lower:
            location_hints.append("Geographic focus: United Kingdom")
        if "usa" in raw_text_lower or "united states" in raw_text_lower or "american" in raw_text_lower:
            location_hints.append("Geographic focus: United States")
        if "canada" in raw_text_lower or "canadian" in raw_text_lower:
            location_hints.append("Geographic focus: Canada")
        
        location_hint_text = f"\nLocation Clues: {'; '.join(location_hints)}" if location_hints else ""
        
        # Prepare content for analysis
        content_text = f"""
        Title: {scraped_content.title or 'N/A'}
        Meta Description: {scraped_content.meta_description or 'N/A'}
        Headings: {', '.join(scraped_content.headings)}
        Main Content: {scraped_content.main_content or 'N/A'}
        Hero Section: {scraped_content.hero_section or 'N/A'}
        Products: {', '.join(scraped_content.products)}
        Contact Info: {scraped_content.contact_info}{location_hint_text}
        """
        
        questions_text = ""
        questions_json_format = ""
        if questions:
            questions_text = f"\n\nCUSTOM QUESTIONS TO ANSWER:\n"
            for i, q in enumerate(questions, 1):
                questions_text += f"{i}. {q}\n"
            
            # Add custom_answers to the expected JSON format
            questions_json_format = ',\n  "custom_answers": {' + ', '.join([f'"{q}": "answer to this question"' for q in questions]) + '}'
        
        prompt = f"""You are an expert business analyst specializing in company profiling. Analyze the following homepage content and extract comprehensive business insights.

Homepage Content: {content_text}

ANALYSIS REQUIREMENTS:

**Industry**: Determine the primary industry/sector. Use inference and context clues if not explicitly stated. Consider business model, products, services, and terminology used.

**Company Size**: Infer company size from indicators like:
- Employee count mentions, team size, office locations
- Scale of operations, client base, market presence
- Use categories: "Startup (1-10)", "Small (11-50)", "Medium (51-200)", "Large (201-1000)", "Enterprise (1000+)"

**Location**: Extract headquarters or primary business location. Look for:
- Physical addresses, "based in", "located in", office locations, contact addresses
- Market focus indicators like "serving Australia", "Australian market", "UK-based"
- Domain extensions (.com.au = Australia, .co.uk = UK, .ca = Canada)
- Geographic terms in title/description (e.g., "Australia & NZ", "European", "US market")
- IMPORTANT: If content mentions "Australia", "New Zealand", "UK", "Canada", "USA" as primary markets, extract that as location

**USP (Unique Selling Proposition)**: Summarize what makes this company unique. Look for:
- Key differentiators, competitive advantages
- Unique features, proprietary technology, special approaches
- Value propositions, mission statements, "why choose us" content

**Products/Services**: List main offerings as simple product/service names. Focus on core business offerings, not features.

**Target Audience**: Infer primary customer demographic from:
- Language tone, imagery descriptions, use cases mentioned
- Pricing tiers, client testimonials, case studies
- Industry focus, problem statements addressed

**Contact Info**: Extract visible contact details (emails, phones, social media handles).
{questions_text}
OUTPUT FORMAT - Return ONLY valid JSON:
{{
  "industry": "specific industry name (required, never null)",
  "company_size": "size category or null if unclear",
  "location": "city, state/country or null if not found (e.g., 'Australia', 'New Zealand', 'United Kingdom', 'United States')",
  "USP": "concise unique value proposition summary or null",
  "products": ["product1", "service1", "offering1"],
  "target_audience": "primary customer demographic description or null",
  "contact_info": {{"emails": [], "phones": [], "social_media": []}}{questions_json_format}
}}

Be thorough in your analysis and use business intelligence to infer details that may not be explicitly stated. For custom questions, provide specific answers based on the website content."""

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
            
            # Clean and structure contact info properly
            contact_info = insights.get("contact_info") or {}
            if not isinstance(contact_info, dict):
                contact_info = {}
            
            # Ensure contact_info has proper structure
            if 'emails' not in contact_info:
                contact_info['emails'] = []
            if 'phones' not in contact_info:
                contact_info['phones'] = []
            if 'social_media' not in contact_info:
                contact_info['social_media'] = []
            
            cleaned_insights = {
                "industry": industry,
                "company_size": insights.get("company_size"),
                "location": insights.get("location"),
                "USP": insights.get("USP"),
                "products": products,
                "target_audience": insights.get("target_audience"),
                "contact_info": contact_info
            }
            
            # Include custom answers if they exist
            if "custom_answers" in insights:
                cleaned_insights["custom_answers"] = insights["custom_answers"]
            
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
