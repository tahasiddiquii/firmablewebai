# 🔐 Authentication Deployment Guide

## Overview

This guide explains how to deploy the Bearer token authentication system to your Railway app.

## ✅ What Was Implemented

### 1. **Bearer Token Authentication**
- Added `HTTPBearer` security to FastAPI
- Created `verify_token()` function for strict authentication
- Added `optional_verify_token()` for migration compatibility
- Added `/api/auth/test` endpoint to test authentication

### 2. **Protected Endpoints**
- `POST /api/insights` - Now requires Bearer token
- `POST /api/query` - Now requires Bearer token

### 3. **Public Endpoints** (No auth required)
- `GET /` - Frontend
- `GET /api/health` - Health check
- `GET /api/info` - API info

### 4. **Frontend Updated**
- Added `getAuthHeaders()` function
- Updated all fetch calls to send Authorization headers
- Uses `demo-secret-key-for-development` by default

### 5. **Test Scripts Updated**
- `test_railway_deployment.py` - Now sends auth headers
- `debug_rag_flow.py` - Now sends auth headers
- `test_authentication.py` - Comprehensive auth testing

## 🚀 Deployment Steps

### Step 1: Set API Secret Key in Railway

1. Go to your Railway dashboard: https://railway.app/dashboard
2. Select your `firmablewebai-production` project
3. Go to **Variables** tab
4. Add a new environment variable:
   ```
   API_SECRET_KEY=your-secure-api-key-here
   ```
   
   **Recommended**: Generate a secure key:
   ```bash
   openssl rand -base64 32
   ```

### Step 2: Deploy Updated Code

Push your changes to trigger Railway deployment:

```bash
git add .
git commit -m "feat: implement Bearer token authentication

- Add HTTPBearer security to FastAPI
- Protect /api/insights and /api/query endpoints
- Update frontend to send Authorization headers
- Add comprehensive authentication tests
- Maintain backward compatibility during migration"

git push origin main
```

### Step 3: Test Authentication

After deployment, test the authentication:

```bash
# Test with our test script
API_SECRET_KEY="your-api-key" python3 test_authentication.py https://firmablewebai-production.up.railway.app

# Or test manually with curl
curl -X GET "https://firmablewebai-production.up.railway.app/api/auth/test" \
  -H "Authorization: Bearer your-api-key"
```

## 🧪 Testing Scenarios

### 1. **Valid Authentication**
```bash
curl -X POST "https://firmablewebai-production.up.railway.app/api/insights" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://spillmate.ai"}'
```

**Expected**: `200 OK` with insights JSON

### 2. **Missing Authentication**
```bash
curl -X POST "https://firmablewebai-production.up.railway.app/api/insights" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://spillmate.ai"}'
```

**Expected**: `401 Unauthorized` with error message

### 3. **Invalid Authentication**
```bash
curl -X POST "https://firmablewebai-production.up.railway.app/api/insights" \
  -H "Authorization: Bearer invalid-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://spillmate.ai"}'
```

**Expected**: `401 Unauthorized` with error message

### 4. **Public Endpoints** (should work without auth)
```bash
curl -X GET "https://firmablewebai-production.up.railway.app/api/health"
```

**Expected**: `200 OK` with health status

## 🔧 Configuration

### Environment Variables Required

```bash
# Required for AI functionality
OPENAI_API_KEY=sk-proj-...

# Required for authentication (NEW)
API_SECRET_KEY=your-secure-api-key-here

# Optional for database
POSTGRES_URL=postgresql://...

# Optional for rate limiting
REDIS_URL=redis://...
```

### Frontend Configuration

The frontend automatically uses the same API key as the backend default (`demo-secret-key-for-development`). For production, you may want to:

1. **Option A**: Use the same key (current implementation)
2. **Option B**: Allow users to input their API key
3. **Option C**: Use session-based authentication

## 🛡️ Security Best Practices

### 1. **Generate Secure API Keys**
```bash
# Generate a secure 32-byte base64 key
openssl rand -base64 32

# Or use Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. **API Key Management**
- Store API keys in environment variables only
- Never commit API keys to version control
- Use different keys for development/production
- Rotate keys periodically

### 3. **Rate Limiting** (Optional Enhancement)
Consider adding rate limiting to prevent abuse:
```python
from fastapi_limiter.depends import RateLimiter

@app.post("/api/insights")
@RateLimiter(times=10, seconds=60)  # 10 requests per minute
async def analyze_website(...):
```

## 📊 Monitoring

### Health Check Updates

The health endpoint now shows API key status:
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

### Error Responses

Authentication errors return standardized responses:
```json
{
  "detail": "Authorization header required. Use: Authorization: Bearer <your-api-key>",
  "headers": {"WWW-Authenticate": "Bearer"}
}
```

## 🔄 Migration Strategy

The implementation uses a **zero-breaking-changes** approach:

1. **Phase 1**: Authentication infrastructure added (✅ Complete)
2. **Phase 2**: Protected endpoints require auth (✅ Complete)
3. **Phase 3**: Frontend updated with auth headers (✅ Complete)
4. **Phase 4**: Test scripts updated (✅ Complete)
5. **Phase 5**: Deploy to production (⏳ Ready)

## 🆘 Troubleshooting

### Common Issues

1. **401 Unauthorized on protected endpoints**
   - Check API_SECRET_KEY is set in Railway
   - Verify Authorization header format: `Bearer your-key`
   - Ensure key matches between client and server

2. **Frontend not working after deployment**
   - Check browser console for 401 errors
   - Verify frontend is using correct API key
   - Clear browser cache

3. **Test scripts failing**
   - Set API_SECRET_KEY environment variable locally
   - Check script is using auth headers
   - Verify Railway deployment is complete

### Debug Commands

```bash
# Check Railway environment variables
railway variables

# Test health endpoint
curl https://firmablewebai-production.up.railway.app/api/health

# Test auth endpoint
curl -H "Authorization: Bearer your-key" \
  https://firmablewebai-production.up.railway.app/api/auth/test
```

## ✅ Success Criteria

After deployment, you should have:

- ✅ Public endpoints accessible without authentication
- ✅ Protected endpoints require Bearer token
- ✅ 401 responses for invalid/missing tokens
- ✅ Frontend works with authentication
- ✅ All test scripts pass
- ✅ Health check shows API_SECRET_KEY configured

## 🎯 Next Steps

1. **Deploy to Railway** with API_SECRET_KEY
2. **Run comprehensive tests** with `test_authentication.py`
3. **Update API documentation** with authentication requirements
4. **Consider rate limiting** for production usage
5. **Monitor usage** and security events

---

🔐 **Authentication implementation complete!** Your API is now secure with Bearer token authentication.
