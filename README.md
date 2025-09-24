# 🤖 FirmableWebAI

**AI-powered backend for extracting business insights from website homepages with RAG-based conversational follow-up.**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

## 🚀 Live Demo

**Production API**: https://firmablewebai-production.up.railway.app

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [API Documentation](#api-documentation)
- [Quick Testing Guide](#quick-testing-guide)
- [Authentication](#authentication)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Testing](#testing)

## 🎯 Overview

FirmableWebAI is a production-ready FastAPI backend that:

1. **Scrapes** homepage content from any website
2. **Extracts** structured business insights using GPT-4.1
3. **Provides** RAG-based conversational Q&A using GPT-4o-mini
4. **Validates** all inputs/outputs with Pydantic
5. **Secures** endpoints with Bearer token authentication

## ✨ Features

- 🔍 **Smart Homepage Scraping** - Extracts title, meta, headings, content, products, contact info
- 🧠 **AI Business Analysis** - Industry, company size, USP, target audience extraction
- 💬 **RAG Conversations** - Ask follow-up questions about analyzed websites
- 🔐 **Bearer Token Auth** - Secure API access with configurable keys
- 📊 **Structured Responses** - Pydantic-validated JSON outputs
- 🚀 **Production Ready** - Deployed on Railway with full error handling

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

## 🔐 Protected Endpoints

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
  "url": "https://spillmate.ai",
  "questions": ["What is their pricing model?", "Who are their competitors?"]
}
```

**Response:**
```json
{
  "industry": "Mental Health Tech",
  "company_size": "Startup (1-10)",
  "location": null,
  "USP": "AI-driven cognitive behavioral therapy with 24/7 availability",
  "products": [
    "Mindful Start",
    "Thrive Plus", 
    "Empower Network"
  ],
  "target_audience": "young adults, students, and professionals seeking stress management",
  "contact_info": {
    "emails": [],
    "phones": [],
    "social_media": []
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
  "url": "https://spillmate.ai",
  "query": "What does this company do?",
  "conversation_history": []
}
```

**Response:**
```json
{
  "answer": "Spillmate is an AI-driven mental health companion that offers personalized support through a chatbot...",
  "source_chunks": [
    "TITLE: Spillmate - Your AI Mental Health Companion...",
    "HERO: Mental Health AI Chatbot..."
  ],
  "conversation_history": [
    {
      "role": "user",
      "content": "What does this company do?"
    },
    {
      "role": "assistant", 
      "content": "Spillmate is an AI-driven mental health companion..."
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
  -d '{"url": "https://spillmate.ai"}'
```
**Expected:** 200 OK with business insights JSON

#### 4. **RAG Query**
```bash
curl -X POST "https://firmablewebai-production.up.railway.app/api/query" \
  -H "Authorization: Bearer VRbGm0B4GUpgYnJQaaa84qzuAX3OJk0LYtbd4xlDlQQ" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://spillmate.ai",
    "query": "What does this company do?",
    "conversation_history": []
  }'
```
**Expected:** 200 OK with conversational answer + source chunks

#### 5. **Authentication Failure** (No Token)
```bash
curl -X POST "https://firmablewebai-production.up.railway.app/api/insights" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://spillmate.ai"}'
```
**Expected:** 401 Unauthorized

#### 6. **Authentication Failure** (Invalid Token)
```bash
curl -X POST "https://firmablewebai-production.up.railway.app/api/insights" \
  -H "Authorization: Bearer invalid-token-123" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://spillmate.ai"}'
```
**Expected:** 401 Unauthorized

### Test Websites
Use these URLs for testing different scenarios:
- `https://spillmate.ai` - Mental Health Tech startup
- `https://stripe.com` - Fintech company  
- `https://openai.com` - AI company
- `https://shopify.com` - E-commerce platform

### Expected Response Times
- Health check: < 1 second
- Authentication: < 1 second  
- Insights analysis: 15-30 seconds (includes scraping + AI processing)
- RAG query: 5-10 seconds

---

## 🔐 Authentication

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

## 🛠 Installation

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

### Automated Tests
```bash
# Run authentication tests
API_SECRET_KEY="your-key" python test_authentication.py https://firmablewebai-production.up.railway.app

# Run RAG flow test  
API_SECRET_KEY="your-key" python debug_rag_flow.py https://firmablewebai-production.up.railway.app https://spillmate.ai

# Run deployment tests
API_SECRET_KEY="your-key" python test_railway_deployment.py https://firmablewebai-production.up.railway.app
```

### Manual Testing
Visit the web interface: https://firmablewebai-production.up.railway.app

---

## 📊 API Response Schemas

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

## 🚀 Deployment

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

## 📈 Performance

- **Scraping**: 2-5 seconds per website
- **AI Analysis**: 10-20 seconds with GPT-4.1
- **RAG Query**: 3-8 seconds with GPT-4o-mini
- **Database**: PostgreSQL with pgvector for embeddings
- **Rate Limiting**: 10 requests/minute per API key

---

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/tahasiddiquii/firmablewebai/issues)
- **Documentation**: This README
- **Testing**: Use provided test scripts

---

## 📄 License

MIT License - see LICENSE file for details.

---

## 🔄 Changelog

### v1.0.0 (Latest)
- ✅ Bearer token authentication
- ✅ Homepage scraping with BeautifulSoup
- ✅ GPT-4.1 business insights extraction
- ✅ RAG-based conversational queries
- ✅ PostgreSQL + pgvector integration
- ✅ Production deployment on Railway
- ✅ Comprehensive test suite
- ✅ Web interface for manual testing

---

**🎯 Ready for production use with full authentication and AI-powered business intelligence!**