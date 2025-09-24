# 🤖 FirmableWebAI

AI-powered backend for extracting business insights from website homepages with RAG-based conversational follow-up.

## ✨ Features

- **🏠 Homepage Scraping**: Extract structured content from any website homepage
- **🧠 AI-Powered Insights**: Generate business insights using GPT-4.1
- **💬 Conversational Q&A**: RAG-based follow-up questions using GPT-4o-mini
- **🔍 Vector Search**: Semantic search using pgvector and text-embedding-3-large
- **🛡️ Security**: Bearer token authentication and rate limiting
- **⚡ Async**: Fully asynchronous, production-ready architecture
- **🚀 Vercel Ready**: Deployable on Vercel serverless functions

## 🏗️ Architecture

```
User → Frontend → API Endpoints → Scrapy Spider → LLMs & Embeddings → pgvector → RAG → Response
```

### Components

- **Frontend Skeleton**: Lightweight HTML/JS interface for demonstration
- **FastAPI Backend**: Async Python web framework with Pydantic validation
- **Scrapy Spider**: Homepage-only content extraction
- **LLM Integration**: GPT-4.1 for insights, GPT-4o-mini for RAG
- **Vector Store**: pgvector for semantic search
- **Database**: PostgreSQL with pgvector extension

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL with pgvector extension
- OpenAI API key
- Redis (optional, for rate limiting)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/firmablewebai.git
   cd firmablewebai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Configure database**
   ```sql
   -- Enable pgvector extension
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

5. **Run tests**
   ```bash
   pytest
   ```

### Local Development

1. **Start the insights API**
   ```bash
   python api/website_insights.py
   ```

2. **Start the query API** (in another terminal)
   ```bash
   python api/website_query.py
   ```

3. **Open the frontend**
   ```bash
   # Serve the frontend files
   cd frontend
   python -m http.server 8000
   ```

## 📡 API Endpoints

### `/website/insights` (POST)

Analyze a website and extract business insights.

**Request:**
```json
{
  "url": "https://example.com",
  "questions": ["What is their main product?", "Who is their target audience?"]
}
```

**Response:**
```json
{
  "industry": "Technology",
  "company_size": "Small",
  "location": "San Francisco",
  "USP": "Innovative solutions",
  "products": ["Product A", "Product B"],
  "target_audience": "Small businesses",
  "contact_info": {
    "emails": ["contact@example.com"],
    "phones": ["+1-555-0123"]
  }
}
```

### `/website/query` (POST)

Ask questions about a previously analyzed website.

**Request:**
```json
{
  "url": "https://example.com",
  "query": "What services do they offer?",
  "conversation_history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"}
  ]
}
```

**Response:**
```json
{
  "answer": "Based on the website content, they offer...",
  "source_chunks": ["Relevant content chunk 1", "Relevant content chunk 2"],
  "conversation_history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"},
    {"role": "user", "content": "What services do they offer?"},
    {"role": "assistant", "content": "Based on the website content, they offer..."}
  ]
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models | Yes |
| `POSTGRES_URL` | PostgreSQL connection string with pgvector | Yes |
| `API_SECRET_KEY` | Secret key for Bearer token authentication | Yes |
| `REDIS_URL` | Redis connection string (optional) | No |

### Database Schema

```sql
CREATE TABLE websites (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    insights JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE website_chunks (
    id SERIAL PRIMARY KEY,
    website_id INT REFERENCES websites(id) ON DELETE CASCADE,
    chunk_text TEXT,
    embedding VECTOR(3072)
);
```

## 🧪 Testing

The project includes comprehensive tests using pytest:

```bash
# Run all tests
pytest

# Run specific test files
pytest tests/test_scraper.py
pytest tests/test_llm_client.py
pytest tests/test_endpoints.py

# Run with coverage
pytest --cov=app --cov=api --cov=models
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Async Tests**: Asynchronous operation testing

## 🚀 Deployment

### Vercel Deployment

1. **Connect to Vercel**
   ```bash
   vercel login
   vercel link
   ```

2. **Set environment variables**
   ```bash
   vercel env add OPENAI_API_KEY
   vercel env add POSTGRES_URL
   vercel env add API_SECRET_KEY
   ```

3. **Deploy**
   ```bash
   vercel --prod
   ```

### Environment Setup

- **OpenAI API**: Get your API key from [OpenAI Platform](https://platform.openai.com/)
- **PostgreSQL**: Use a service like [Neon](https://neon.tech/) or [Supabase](https://supabase.com/) with pgvector
- **Redis**: Optional, for rate limiting (use [Upstash](https://upstash.com/) for serverless)

## 📁 Project Structure

```
firmablewebai/
├── api/                    # FastAPI endpoints
│   ├── website_insights.py # Insights generation endpoint
│   └── website_query.py    # RAG query endpoint
├── app/                    # Core application logic
│   ├── db/                 # Database client
│   ├── llm/               # LLM integration
│   └── scraper/           # Web scraping
├── models/                 # Pydantic models
├── frontend/              # Demo frontend
├── tests/                  # Test suite
├── requirements.txt        # Dependencies
├── vercel.json            # Vercel configuration
└── README.md              # This file
```

## 🔒 Security

- **Authentication**: Bearer token required for all endpoints
- **Rate Limiting**: Configurable rate limits per endpoint
- **Input Validation**: Pydantic models validate all inputs
- **Error Handling**: Graceful error handling and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join the community discussions

## 🎯 Roadmap

- [ ] Enhanced scraping capabilities
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] API rate limiting improvements
- [ ] Caching layer implementation
- [ ] Webhook support for real-time updates

---

**Built with ❤️ using FastAPI, Scrapy, OpenAI, and pgvector**