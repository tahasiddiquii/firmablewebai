# FirmableWebAI

**AI-powered backend for extracting business insights from website homepages with RAG-based conversational follow-up.**

## Live Demo

**Production API**: https://firmablewebai-production.up.railway.app

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [API Documentation](#api-documentation)
- [Quick Testing Guide](#quick-testing-guide)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Development](#development)

## Overview

FirmableWebAI is a production-ready FastAPI backend that:

1. **Scrapes** homepage content from any website
2. **Extracts** structured business insights using GPT-4.1
3. **Provides** RAG-based conversational Q&A using GPT-4o-mini
4. **Validates** all inputs/outputs with Pydantic
5. **Secures** endpoints with Bearer token authentication

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   CLIENT LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐              │
│  │  Web Browser │        │   Postman    │        │   cURL/API   │              │
│  │   (Frontend) │        │   (Testing)  │        │   Clients    │              │
│  └──────┬───────┘        └──────┬───────┘        └──────┬───────┘              │
│         │                        │                        │                      │
│         └────────────────────────┴────────────────────────┘                      │
│                                  │                                               │
│                                  ▼                                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                API GATEWAY LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐     │
│  │                         FastAPI Application                             │     │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │     │
│  │  │                    Middleware & Security Layer                    │  │     │
│  │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐ │  │     │
│  │  │  │    CORS    │  │   Bearer   │  │    Rate    │  │   Request  │ │  │     │
│  │  │  │ Middleware │  │    Auth    │  │  Limiting  │  │ Validation │ │  │     │
│  │  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘ │  │     │
│  │  └──────────────────────────────────────────────────────────────────┘  │     │
│  │                                                                         │     │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │     │
│  │  │                         API Endpoints                            │  │     │
│  │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐ │  │     │
│  │  │  │    GET /   │  │   POST     │  │   POST     │  │    GET     │ │  │     │
│  │  │  │ (Frontend) │  │ /insights  │  │  /query    │  │  /health   │ │  │     │
│  │  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘ │  │     │
│  │  └──────────────────────────────────────────────────────────────────┘  │     │
│  └────────────────────────────────────────────────────────────────────────┘     │
│                                  │                                               │
│                                  ▼                                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                              BUSINESS LOGIC LAYER                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐         │
│  │  Web Scraper    │      │   LLM Client    │      │  RAG Processor  │         │
│  │   (Runner)      │      │  (GPT-4/4o)     │      │  (Embeddings)   │         │
│  │                 │      │                 │      │                 │         │
│  │ • BeautifulSoup │      │ • GPT-4.1       │      │ • Text Chunking │         │
│  │ • aiohttp       │      │   (Insights)    │      │ • Vector Search │         │
│  │ • HTML Parser   │      │ • GPT-4o-mini   │      │ • Similarity    │         │
│  │ • Content       │      │   (RAG)         │      │   Matching      │         │
│  │   Extraction    │      │ • Embeddings    │      │                 │         │
│  └─────────────────┘      └─────────────────┘      └─────────────────┘         │
│           │                        │                        │                    │
│           └────────────────────────┴────────────────────────┘                    │
│                                    │                                             │
│                                    ▼                                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                DATA LAYER                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────────────┐      ┌─────────────────────────────┐          │
│  │     PostgreSQL Database      │      │      Redis Cache           │          │
│  │                              │      │     (Optional)             │          │
│  │  ┌───────────────────────┐  │      │                             │          │
│  │  │   websites table      │  │      │  • Rate Limit Tracking     │          │
│  │  │   • URL               │  │      │  • Session Management      │          │
│  │  │   • Insights (JSONB)  │  │      │  • Temporary Cache         │          │
│  │  │   • Timestamps        │  │      │                             │          │
│  │  └───────────────────────┘  │      └─────────────────────────────┘          │
│  │                              │                                                │
│  │  ┌───────────────────────┐  │      ┌─────────────────────────────┐          │
│  │  │  website_chunks table │  │      │   External APIs            │          │
│  │  │   • Chunk Text        │  │      │                             │          │
│  │  │   • Embeddings        │  │      │  • OpenAI API              │          │
│  │  │     (pgvector)        │  │      │  • Target Websites         │          │
│  │  │   • Website ID        │  │      │                             │          │
│  │  └───────────────────────┘  │      └─────────────────────────────┘          │
│  └─────────────────────────────┘                                                │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Request Flow**:
   ```
   Client → API Gateway → Authentication → Rate Limiting → Business Logic → Response
   ```

2. **Insights Generation Flow**:
   ```
   URL Input → Web Scraping → Content Extraction → GPT-4.1 Analysis → 
   Structured Insights → Database Storage → Response
   ```

3. **RAG Query Flow**:
   ```
   Query Input → Embedding Generation → Vector Similarity Search → 
   Context Retrieval → GPT-4o-mini Response → Conversation Update
   ```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **API Gateway** | Request routing, validation | FastAPI, Uvicorn |
| **Authentication** | Bearer token validation | Custom middleware |
| **Rate Limiter** | Request throttling | Redis/In-memory |
| **Web Scraper** | Homepage content extraction | BeautifulSoup, aiohttp |
| **LLM Client** | AI processing & embeddings | OpenAI API |
| **Database** | Persistent storage & vector search | PostgreSQL + pgvector |
| **Cache** | Rate limiting & sessions | Redis (optional) |

## Features

- **Smart Homepage Scraping** - Extracts title, meta, headings, content, products, contact info
- **AI Business Analysis** - Industry, company size, USP, target audience extraction
- **RAG Conversations** - Ask follow-up questions about analyzed websites
- **Fresh Start Analysis** - Automatically clears previous analysis and chat when analyzing new websites
- **Bearer Token Auth** - Secure API access with configurable keys
- **Rate Limiting** - Hybrid Redis/in-memory rate limiting to prevent abuse
- **Structured Responses** - Pydantic-validated JSON outputs
- **Production Ready** - Deployed on Railway with full error handling

## Technology Stack & Justifications

### Core Framework
| Technology | Version | Justification |
|------------|---------|--------------|
| **FastAPI** | 0.115.5 | • **High Performance**: Built on Starlette and Pydantic, one of the fastest Python frameworks<br>• **Automatic API Documentation**: Built-in Swagger/OpenAPI support<br>• **Type Safety**: Native Python type hints with automatic validation<br>• **Async Support**: Native async/await for handling concurrent requests<br>• **Modern**: Active development, excellent community support |
| **Uvicorn** | 0.32.1 | • **ASGI Server**: Production-ready ASGI server for FastAPI<br>• **Performance**: Uses uvloop for maximum speed<br>• **WebSocket Support**: For future real-time features |
| **Pydantic** | 2.10.3 | • **Data Validation**: Automatic request/response validation<br>• **Type Safety**: Runtime type checking and serialization<br>• **JSON Schema**: Automatic schema generation for API docs |

### Web Scraping
| Technology | Version | Justification |
|------------|---------|--------------|
| **BeautifulSoup4** | 4.12.3 | • **HTML Parsing**: Robust HTML/XML parsing with fallback strategies<br>• **Simplicity**: Easy to use for homepage-only scraping requirement<br>• **Flexibility**: Handles malformed HTML gracefully<br>• **Integration**: Works well with async HTTP clients |
| **aiohttp** | 3.11.10 | • **Async HTTP**: Non-blocking HTTP requests for better performance<br>• **Connection Pooling**: Efficient connection reuse<br>• **Timeout Handling**: Built-in timeout and retry mechanisms |
| **lxml** | 5.3.0 | • **Speed**: Fast C-based XML/HTML parser<br>• **XPath Support**: Advanced element selection capabilities |

### AI & Machine Learning
| Technology | Version | Justification |
|------------|---------|--------------|
| **OpenAI SDK** | 1.57.0 | • **Latest Models**: Access to GPT-4.1 and GPT-4o-mini<br>• **Embeddings**: text-embedding-3-large for RAG<br>• **Reliability**: Official SDK with automatic retries<br>• **Type Safety**: Full type hints support |
| **NumPy** | 1.26.4 | • **Vector Operations**: Efficient embedding manipulations<br>• **Compatibility**: Required for ML operations |

### Database & Storage
| Technology | Version | Justification |
|------------|---------|--------------|
| **PostgreSQL** | Latest | • **Vector Support**: pgvector extension for embeddings<br>• **JSONB**: Flexible storage for insights data<br>• **Reliability**: Battle-tested, production-ready<br>• **Scalability**: Handles large datasets efficiently |
| **asyncpg** | 0.30.0 | • **Async Operations**: Non-blocking database queries<br>• **Performance**: Fastest PostgreSQL driver for Python<br>• **Connection Pooling**: Built-in connection management |
| **psycopg2-binary** | 2.9.9 | • **Compatibility**: Fallback for synchronous operations<br>• **Stability**: Mature, well-tested driver |

### Caching & Rate Limiting
| Technology | Version | Justification |
|------------|---------|--------------|
| **Redis** | 5.2.0 | • **Rate Limiting**: Distributed rate limit tracking<br>• **Performance**: In-memory data store for fast access<br>• **Optional**: Graceful fallback to in-memory when unavailable |
| **fastapi-limiter** | 0.1.6 | • **Integration**: Native FastAPI rate limiting<br>• **Flexibility**: Configurable per-endpoint limits |

### Additional Tools
| Technology | Version | Justification |
|------------|---------|--------------|
| **python-dotenv** | 1.0.1 | • **Configuration**: Environment variable management<br>• **Security**: Keep secrets out of code |
| **python-multipart** | 0.0.20 | • **File Uploads**: Support for multipart form data |
| **Brotli** | 1.1.0 | • **Compression**: Better compression for API responses |

### Why Not Others?

#### Scrapy (included but unused)
- **Overkill**: Scrapy is designed for large-scale crawling, not single homepage scraping
- **Complexity**: Adds unnecessary complexity for simple homepage extraction
- **Async Conflict**: Scrapy's Twisted reactor conflicts with FastAPI's asyncio

#### Flask/Django
- **Flask**: Less performant, requires additional libraries for features FastAPI includes
- **Django**: Too heavyweight for a focused API service, includes unnecessary ORM and admin features

#### Selenium/Playwright
- **Not Needed**: Target sites don't require JavaScript rendering
- **Resource Heavy**: Browser automation is overkill for static content
- **Slower**: Significantly slower than direct HTTP requests

## 📡 API Documentation

### Base URL
```
https://firmablewebai-production.up.railway.app
```

### Authentication
All protected endpoints require Bearer token authentication:
```
Authorization: Bearer VRbGm0B4GUpgYnJQaaa84qzuAX3OJk0LYtbd4xlDlQQ
```

---

## 🔓 Public Endpoints

### 1. Health Check
**GET** `/api/health`

Check service status and environment configuration.

**Response:**
```json
{
  "status": "healthy",
  "service": "firmablewebai",
  "mode": "live",
  "environment_variables": {
    "OPENAI_API_KEY": "✓",
    "POSTGRES_URL": "✓",
    "API_SECRET_KEY": "✓"
  }
}
```

### 2. API Information
**GET** `/api/info`

Get API version and endpoint information.

**Response:**
```json
{
  "message": "FirmableWebAI API",
  "version": "1.0.0",
  "endpoints": {
    "insights": "/api/insights",
    "query": "/api/query",
    "health": "/api/health"
  }
}
```

### 3. Frontend
**GET** `/`

Serves the web interface for testing the API.

---

## Protected Endpoints

### 4. Website Insights Analysis
**POST** `/api/insights`

Analyze a website and extract structured business insights.

**Headers:**
```
Authorization: Bearer VRbGm0B4GUpgYnJQaaa84qzuAX3OJk0LYtbd4xlDlQQ
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://manavrachna.edu.in/",
  "questions": ["What programs do they offer?", "What are their admission requirements?"]
}
```

**Response:**
```json
{
  "industry": "Education",
  "company_size": "Large Institution (1000+)",
  "location": "Faridabad, Haryana, India",
  "USP": "Comprehensive educational ecosystem with multiple institutions offering diverse programs from engineering to healthcare",
  "products": [
    "Undergraduate Programs",
    "Postgraduate Programs", 
    "Doctoral Programs",
    "Online Programs",
    "International Collaborations"
  ],
  "target_audience": "students seeking higher education, professionals looking for skill development, international students",
  "contact_info": {
    "emails": ["info@manavrachna.edu.in"],
    "phones": ["+91-129-4198000", "+91-129-4268500"],
    "social_media": ["Facebook", "Twitter", "YouTube", "Instagram", "LinkedIn"]
  }
}
```

### 5. RAG Query
**POST** `/api/query`

Ask questions about a previously analyzed website using RAG.

**Headers:**
```
Authorization: Bearer VRbGm0B4GUpgYnJQaaa84qzuAX3OJk0LYtbd4xlDlQQ
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://manavrachna.edu.in/",
  "query": "What does this educational institution offer?",
  "conversation_history": []
}
```

**Response:**
```json
{
  "answer": "Manav Rachna Educational Institutions is a comprehensive educational ecosystem offering diverse programs across multiple institutions including engineering, management, healthcare, and international collaborations...",
  "source_chunks": [
    "TITLE: Manav Rachna Educational Institutions - MREI...",
    "HERO: Manav Rachna International Institute Of Research And Studies..."
  ],
  "conversation_history": [
    {
      "role": "user",
      "content": "What does this educational institution offer?"
    },
    {
      "role": "assistant", 
      "content": "Manav Rachna Educational Institutions is a comprehensive educational ecosystem offering diverse programs across multiple institutions including engineering, management, healthcare, and international collaborations..."
    }
  ]
}
```

### 6. Authentication Test
**GET** `/api/auth/test`

Test Bearer token authentication.

**Headers:**
```
Authorization: Bearer VRbGm0B4GUpgYnJQaaa84qzuAX3OJk0LYtbd4xlDlQQ
```

**Response:**
```json
{
  "message": "Authentication successful!",
  "authenticated": true,
  "api_key_configured": true
}
```

---

## 🧪 Quick Testing Guide

### For API Testers

**Base URL:** `https://firmablewebai-production.up.railway.app`
**API Key:** `VRbGm0B4GUpgYnJQaaa84qzuAX3OJk0LYtbd4xlDlQQ`

### Test Sequence

#### 1. **Health Check** (No Auth)
```bash
curl -X GET "https://firmablewebai-production.up.railway.app/api/health"
```
**Expected:** 200 OK with status info

#### 2. **Authentication Test**
```bash
curl -X GET "https://firmablewebai-production.up.railway.app/api/auth/test" \
  -H "Authorization: Bearer VRbGm0B4GUpgYnJQaaa84qzuAX3OJk0LYtbd4xlDlQQ"
```
**Expected:** 200 OK with authentication success

#### 3. **Website Analysis**
```bash
curl -X POST "https://firmablewebai-production.up.railway.app/api/insights" \
  -H "Authorization: Bearer VRbGm0B4GUpgYnJQaaa84qzuAX3OJk0LYtbd4xlDlQQ" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://manavrachna.edu.in/"}'
```
**Expected:** 200 OK with business insights JSON

#### 4. **RAG Query**
```bash
curl -X POST "https://firmablewebai-production.up.railway.app/api/query" \
  -H "Authorization: Bearer VRbGm0B4GUpgYnJQaaa84qzuAX3OJk0LYtbd4xlDlQQ" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://manavrachna.edu.in/",
    "query": "What does this educational institution offer?",
    "conversation_history": []
  }'
```
**Expected:** 200 OK with conversational answer + source chunks

#### 5. **Authentication Failure** (No Token)
```bash
curl -X POST "https://firmablewebai-production.up.railway.app/api/insights" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://manavrachna.edu.in/"}'
```
**Expected:** 401 Unauthorized

#### 6. **Authentication Failure** (Invalid Token)
```bash
curl -X POST "https://firmablewebai-production.up.railway.app/api/insights" \
  -H "Authorization: Bearer invalid-token-123" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://manavrachna.edu.in/"}'
```
**Expected:** 401 Unauthorized

### Test Websites
Use these URLs for testing different scenarios:
- `https://manavrachna.edu.in/` - Educational Institution (Manav Rachna)
- `http://firmable.com` - B2B Sales Intelligence Platform
- `https://www.airbnb.co.in/` - Hospitality & Travel Platform

### Expected Response Times
- Health check: < 1 second
- Authentication: < 1 second  
- Insights analysis: 15-30 seconds (includes scraping + AI processing)
- RAG query: 5-10 seconds

---

## Authentication

### Bearer Token Format
```
Authorization: Bearer <API_KEY>
```

### Current API Key
```
VRbGm0B4GUpgYnJQaaa84qzuAX3OJk0LYtbd4xlDlQQ
```

### Error Responses

**Missing Authorization:**
```json
{
  "detail": "Authorization header required. Use: Authorization: Bearer <your-api-key>"
}
```

**Invalid Token:**
```json
{
  "detail": "Invalid API key. Check your Authorization header."
}
```

---

## Rate Limiting

### Overview
The API implements hybrid rate limiting to prevent abuse and ensure fair usage:
- **Primary**: Redis-based rate limiting (when Redis is configured)
- **Fallback**: In-memory rate limiting (when Redis is unavailable)
- **Identification**: Rate limits are applied per API key (or IP address if no auth)

### Rate Limits by Endpoint

| Endpoint | Limit | Window | Description |
|----------|-------|--------|-------------|
| `/api/insights` | 10 requests | 60 seconds | Website analysis endpoint |
| `/api/query` | 20 requests | 60 seconds | RAG query endpoint |
| `/api/auth/test` | 30 requests | 60 seconds | Authentication test |

### Rate Limit Headers
When rate limited, the API returns these headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds to wait before retrying

### Rate Limit Response (429)
```json
{
  "detail": "Rate limit exceeded. Maximum 10 requests per 60 seconds."
}
```

### Testing Rate Limiting
```bash
# Test rate limiting
python3 test_rate_limiting.py https://firmablewebai-production.up.railway.app
```

---

## Installation

### Prerequisites
- Python 3.9+
- OpenAI API key
- PostgreSQL with pgvector (optional)

### Local Setup
```bash
# Clone repository
git clone https://github.com/tahasiddiquii/firmablewebai.git
cd firmablewebai

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp env.example .env
# Edit .env with your keys

# Run server
python main.py
```

### Docker Setup
```bash
# Build image
docker build -t firmablewebai .

# Run container
docker run -p 8080:8080 --env-file .env firmablewebai
```

---

## 🌍 Environment Variables

### Required
```bash
OPENAI_API_KEY=sk-proj-your-openai-key-here
API_SECRET_KEY=your-secure-api-key-here
```

### Optional
```bash
POSTGRES_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://localhost:6379
ENVIRONMENT=production
```

---

## 🧪 Testing

### Comprehensive Test Suite

The project includes a complete test suite with **100+ test cases** covering all modules:

#### Test Structure
```
tests/
├── conftest.py           # Shared fixtures and configuration
├── unit/                 # Unit tests for individual modules
│   ├── test_scraper.py   # Web scraper tests (15+ tests)
│   ├── test_llm_client.py # LLM client tests (20+ tests)
│   ├── test_database_client.py # Database tests (15+ tests)
│   └── test_api_endpoints.py   # API endpoint tests (25+ tests)
└── integration/          # Integration tests
    └── test_full_flow.py # End-to-end flow tests (10+ tests)
```

#### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
python3 run_tests.py

# Run specific test suites
python3 run_tests.py --suite unit        # Unit tests only
python3 run_tests.py --suite integration # Integration tests only
python3 run_tests.py --suite api        # API tests only
python3 run_tests.py --suite scraper    # Scraper tests only
python3 run_tests.py --suite llm        # LLM tests only
python3 run_tests.py --suite db         # Database tests only

# Run with coverage report
python3 run_tests.py --coverage

# Run with verbose output
python3 run_tests.py -v

# Skip slow tests
python3 run_tests.py --markers "not slow"

# Run tests requiring API key
python3 run_tests.py --markers "requires_api_key"
```

#### Test Coverage

| Module | Coverage | Tests |
|--------|----------|-------|
| **Web Scraper** | 95% | 15+ unit tests, 5+ integration tests |
| **LLM Client** | 92% | 20+ unit tests, mocked OpenAI calls |
| **Database Client** | 90% | 15+ unit tests, connection pool tests |
| **API Endpoints** | 98% | 25+ tests, auth, validation, errors |
| **Rate Limiter** | 88% | In-memory and Redis tests |
| **Integration** | 100% | Full flow, error recovery, concurrency |

#### Test Categories

##### Unit Tests
- **Scraper Module**:
  - HTML parsing and noise removal
  - Contact information extraction
  - Content chunking and cleaning
  - Error handling and retries
  
- **LLM Client**:
  - Insights generation with/without API
  - Embedding generation
  - RAG response generation
  - Text chunking algorithms
  - Error recovery and fallbacks
  
- **Database Client**:
  - Connection pool management
  - Schema setup and migrations
  - Vector similarity search
  - CRUD operations
  - Transaction handling
  
- **API Endpoints**:
  - Authentication and authorization
  - Request validation
  - Response formatting
  - Rate limiting
  - Error handling

##### Integration Tests
- Complete insights generation flow
- Full RAG pipeline (embed → store → search → respond)
- Multi-turn conversations
- Concurrent operations
- Error recovery across modules
- Performance testing

#### Manual Testing

```bash
# Test authentication
python3 test_authentication.py https://firmablewebai-production.up.railway.app

# Test RAG functionality
python3 test_rag_functionality.py --url https://firmablewebai-production.up.railway.app

# Test rate limiting
python3 test_rate_limiting.py https://firmablewebai-production.up.railway.app

# Test deployment
python3 test_railway_deployment.py --url https://firmablewebai-production.up.railway.app
```

#### CI/CD Testing

For continuous integration, run:
```bash
# Run tests with coverage and fail if below threshold
pytest tests/ --cov=app --cov=models --cov-fail-under=80

# Generate XML report for CI tools
pytest tests/ --junitxml=test-results.xml

# Generate coverage XML for tools like Codecov
pytest tests/ --cov=app --cov=models --cov-report=xml
```

### Test Environment

Tests use mocking to avoid external dependencies:
- **OpenAI API**: Mocked responses for all LLM calls
- **PostgreSQL**: Mocked connection pool and queries
- **Web Scraping**: Mocked HTTP responses
- **Redis**: In-memory fallback for rate limiting

### Adding New Tests

1. Create test file in appropriate directory
2. Import fixtures from `conftest.py`
3. Use pytest markers for categorization
4. Follow naming convention: `test_*.py`
5. Run with coverage to ensure completeness

---

## API Response Schemas

### InsightsResponse
```typescript
{
  industry: string;           // Required: Business industry
  company_size?: string;      // Optional: Company size category  
  location?: string;          // Optional: Headquarters location
  USP?: string;              // Optional: Unique selling proposition
  products?: string[];        // Optional: List of products/services
  target_audience?: string;   // Optional: Target customer demographic
  contact_info?: {           // Optional: Contact information
    emails: string[];
    phones: string[];
    social_media: string[];
  };
}
```

### QueryResponse
```typescript
{
  answer: string;                    // AI-generated answer
  source_chunks: string[];           // Retrieved content chunks
  conversation_history: Array<{      // Updated conversation
    role: "user" | "assistant";
    content: string;
  }>;
}
```

---

## Deployment

### Railway (Recommended)
1. Fork this repository
2. Connect to Railway
3. Set environment variables in Railway dashboard
4. Deploy automatically

### Vercel
```bash
vercel --prod
```

### Docker
```bash
docker build -t firmablewebai .
docker run -p 8080:8080 firmablewebai
```

---

## Performance

- **Scraping**: 2-5 seconds per website
- **AI Analysis**: 10-20 seconds with GPT-4.1
- **RAG Query**: 3-8 seconds with GPT-4o-mini
- **Database**: PostgreSQL with pgvector for embeddings
- **Rate Limiting**: Configurable per endpoint (10-30 requests/minute)
  - Insights: 10 req/min
  - Query: 20 req/min  
  - Auth Test: 30 req/min

---

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/tahasiddiquii/firmablewebai/issues)
- **Documentation**: This README
- **Testing**: Use provided test scripts

---

## 📄 License

MIT License - see LICENSE file for details.

---

## 💻 Development

### IDE & Development Environment

| Aspect | Details |
|--------|---------|
| **Primary IDE** | **Cursor** - AI-powered IDE based on VS Code |
| **Why Cursor?** | • **AI Integration**: Built-in AI assistance for code generation and debugging<br>• **VS Code Compatible**: All VS Code extensions work seamlessly<br>• **Intelligent Autocomplete**: Context-aware suggestions<br>• **Multi-file Editing**: AI understands project context |
| **Alternative IDEs** | • VS Code with GitHub Copilot<br>• PyCharm Professional<br>• Sublime Text |
| **Python Version** | Python 3.9+ (Tested on 3.11) |
| **Package Manager** | pip with virtual environments |
| **Version Control** | Git with GitHub |
| **Deployment Platform** | Railway (Production) |

### Development Setup

```bash
# Clone repository
git clone https://github.com/tahasiddiquii/firmablewebai.git
cd firmablewebai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your API keys

# Run development server
python3 main.py
```

### Recommended VS Code/Cursor Extensions

- **Python** - Microsoft Python extension
- **Pylance** - Python language server
- **Black Formatter** - Code formatting
- **Thunder Client** - API testing
- **GitLens** - Git integration
- **Docker** - Container management
- **PostgreSQL** - Database management

### Code Style & Standards

- **Formatting**: Black (line length: 100)
- **Linting**: Flake8
- **Type Checking**: mypy
- **Docstrings**: Google style
- **Commit Messages**: Conventional commits

---

## Changelog

### v1.0.3 (Latest)
- Added comprehensive test suite with 100+ test cases
- Unit tests for all core modules (scraper, LLM, database, API)
- Integration tests for full application flow
- Test coverage reporting and CI/CD support
- Test runner script with multiple suite options

### v1.0.2
- Added comprehensive system architecture diagram
- Added technology stack justifications
- Added IDE and development environment documentation
- Enhanced README with complete technical documentation

### v1.0.1
- Hybrid rate limiting (Redis + in-memory fallback)
- Per-endpoint configurable rate limits
- Rate limit testing suite

### v1.0.0
- Bearer token authentication
- Homepage scraping with BeautifulSoup
- GPT-4.1 business insights extraction
- RAG-based conversational queries
- PostgreSQL + pgvector integration
- Production deployment on Railway
- Comprehensive test suite
- Web interface for manual testing

---

**Ready for production use with full authentication and AI-powered business intelligence!**