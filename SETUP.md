# FirmableWebAI Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Configure Environment
```bash
python3 configure.py
```

### 3. Get OpenAI API Key

#### Option A: Get a Real OpenAI API Key (Recommended)
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Go to **API Keys** section
4. Click **Create new secret key**
5. Copy the key (starts with `sk-...`)
6. Edit `.env` file and replace `sk-your-openai-api-key-here` with your actual key

#### Option B: Use Test Mode (For Development)
If you don't have an OpenAI API key yet, you can use test mode:
```bash
python3 test_mode.py
```

### 4. Start the Application
```bash
python3 main.py
```

### 5. Access the Application
- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Environment Variables

Create a `.env` file with:

```env
# Required for full functionality
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Optional (for advanced features)
POSTGRES_URL=postgresql://username:password@localhost:5432/firmablewebai
REDIS_URL=redis://localhost:6379
API_SECRET_KEY=your_secure_api_secret_key_here
```

## Testing

### Test with Real API
```bash
curl -X POST http://localhost:8000/api/insights \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Test Mode (No API Key Required)
```bash
python3 test_mode.py --url https://example.com
```

## Troubleshooting

### Common Issues

1. **"Service not available - OpenAI API key not configured"**
   - Make sure you have a valid OpenAI API key in your `.env` file
   - Run `python3 configure.py` to verify configuration

2. **"Connection refused" errors**
   - Redis/PostgreSQL are optional for basic functionality
   - The app will work without them (with degraded features)

3. **Import errors**
   - Run `pip3 install -r requirements.txt`
   - Make sure you're using Python 3.8+

### Getting Help

1. Check the logs: The application provides detailed logging
2. Test endpoints: Use `/api/health` to check service status
3. API Documentation: Visit `/docs` for interactive API testing

## Deployment

### Railway (Recommended)
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard:
   - `OPENAI_API_KEY=your_key_here`
   - `POSTGRES_URL=your_postgres_url` (optional)
3. Deploy automatically

### Vercel
1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel`
3. Set environment variables in Vercel dashboard

### Local Production
```bash
# Install production dependencies
pip3 install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_key_here

# Start with gunicorn (production server)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## Features

### Core Features (Require OpenAI API Key)
- ✅ Website scraping and analysis
- ✅ AI-powered business insights extraction
- ✅ RAG-based conversational queries
- ✅ Vector embeddings and similarity search

### Optional Features (Require Additional Setup)
- 🔄 Database persistence (PostgreSQL + pgvector)
- 🔄 Rate limiting (Redis)
- 🔄 Advanced caching

### Test Mode Features (No API Key Required)
- ✅ Website scraping
- ✅ Mock insights generation
- ✅ Frontend functionality testing
- ✅ API endpoint testing

## Next Steps

1. **Get OpenAI API Key**: Essential for full functionality
2. **Set up PostgreSQL**: For conversation history and vector search
3. **Configure Redis**: For rate limiting and caching
4. **Deploy to Production**: Railway, Vercel, or your preferred platform

Happy coding! 🚀
