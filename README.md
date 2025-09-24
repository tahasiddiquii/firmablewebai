# 🤖 FirmableWebAI

AI-powered backend for extracting business insights from website homepages with RAG-based conversational follow-up.

## ✨ Features

- **🏠 Homepage Scraping**: Extract structured content from any website homepage
- **🧠 AI-Powered Insights**: Generate business insights using GPT-4.1
- **💬 Conversational Q&A**: RAG-based follow-up questions using GPT-4o-mini
- **🔍 Vector Search**: Semantic search using pgvector and text-embedding-3-large
- **🛡️ Security**: Bearer token authentication and rate limiting
- **⚡ Async**: Fully asynchronous, production-ready architecture
- **🚂 Railway Ready**: Deployable on Railway with persistent connections

## 🏗️ Architecture

```
User → Frontend → FastAPI App → Scrapy Spider → LLMs & Embeddings → pgvector → RAG → Response
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

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Run tests** (optional)
   ```bash
   pytest
   ```

### Local Development

1. **Start the unified FastAPI application**
   ```bash
   python main.py
   ```
   
   This starts the server on `http://localhost:8000` with:
   - API endpoints at `/api/*`
   - Frontend served from root `/`
   - Interactive docs at `/docs`

2. **Test the API**
   ```bash
   # Health check
   curl http://localhost:8000/api/health
   
   # Website analysis (demo mode)
   curl -X POST http://localhost:8000/api/insights \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer demo-token-123" \
     -d '{"url": "https://openai.com"}'
   ```

## 📡 API Endpoints

### `/api/insights` (POST)

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

### `/api/query` (POST)

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

### Railway Deployment

1. **Create Railway Project**
   - Go to [Railway.app](https://railway.app)
   - Sign up with GitHub
   - Create new project from your GitHub repository

2. **Configure Environment Variables**
   ```bash
   OPENAI_API_KEY=sk-your-actual-openai-key-here
   POSTGRES_URL=postgresql://user:password@host:5432/database
   API_SECRET_KEY=y7H9r!Pz3qT8mLw#Xv2Bf@Kc5jS1dG6n
   ```

3. **Deploy**
   - Railway automatically deploys on push
   - View logs and manage from Railway dashboard

For detailed deployment instructions, see [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)

### Environment Setup

- **OpenAI API**: Get your API key from [OpenAI Platform](https://platform.openai.com/)
- **PostgreSQL**: Use Railway PostgreSQL plugin or [Supabase](https://supabase.com/) with pgvector
- **Redis**: Optional, for rate limiting

## 📁 Project Structure

```
firmablewebai/
├── main.py                 # Unified FastAPI application
├── api/                    # Legacy API files (for reference)
├── app/                    # Core application logic
│   ├── db/                 # Database client
│   ├── llm/               # LLM integration
│   └── scraper/           # Web scraping
├── models/                 # Pydantic models
├── frontend/              # Demo frontend
├── public/                # Static files served by FastAPI
├── tests/                  # Test suite
├── requirements.txt        # Dependencies
├── Procfile               # Railway process definition
├── railway.toml           # Railway configuration
├── nixpacks.toml          # Build configuration
├── test_railway.py        # Railway deployment testing
├── RAILWAY_DEPLOYMENT.md  # Deployment guide
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