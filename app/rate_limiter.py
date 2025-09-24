"""
Rate Limiting Module for FirmableWebAI
Provides both Redis-based and in-memory rate limiting
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from fastapi import HTTPException, Request
import hashlib
import os

# Try to import Redis components
try:
    import redis
    from fastapi_limiter import FastAPILimiter
    from fastapi_limiter.depends import RateLimiter as RedisRateLimiter
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    RedisRateLimiter = None


class InMemoryRateLimiter:
    """
    In-memory rate limiter as fallback when Redis is not available.
    Uses a sliding window algorithm.
    """
    
    def __init__(self):
        # Store request timestamps for each client
        # Format: {client_id: deque([(timestamp, count), ...])}
        self._requests: Dict[str, deque] = defaultdict(lambda: deque())
        self._lock = asyncio.Lock()
        
    def _get_client_id(self, request: Request, api_key: Optional[str] = None) -> str:
        """Generate a unique client identifier"""
        if api_key:
            # Use API key as primary identifier
            return hashlib.md5(api_key.encode()).hexdigest()
        
        # Fallback to IP address
        client_host = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        
        if forwarded_for:
            # Handle proxied requests
            client_host = forwarded_for.split(",")[0].strip()
        
        return hashlib.md5(client_host.encode()).hexdigest()
    
    async def check_rate_limit(
        self, 
        request: Request, 
        times: int = 10, 
        seconds: int = 60,
        api_key: Optional[str] = None
    ) -> bool:
        """
        Check if the client has exceeded the rate limit.
        
        Args:
            request: FastAPI request object
            times: Maximum number of requests allowed
            seconds: Time window in seconds
            api_key: Optional API key for identification
            
        Returns:
            True if request is allowed, raises HTTPException if rate limited
        """
        async with self._lock:
            client_id = self._get_client_id(request, api_key)
            current_time = time.time()
            window_start = current_time - seconds
            
            # Get client's request history
            client_requests = self._requests[client_id]
            
            # Remove old requests outside the window
            while client_requests and client_requests[0] < window_start:
                client_requests.popleft()
            
            # Check if limit is exceeded
            if len(client_requests) >= times:
                # Calculate time until oldest request expires
                oldest_request = client_requests[0]
                retry_after = int(oldest_request + seconds - current_time) + 1
                
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Maximum {times} requests per {seconds} seconds.",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(times),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(oldest_request + seconds))
                    }
                )
            
            # Add current request to history
            client_requests.append(current_time)
            
            # Set rate limit headers
            remaining = times - len(client_requests)
            reset_time = int(current_time + seconds)
            
            # Note: Headers need to be set in the response, not here
            # This is just for tracking
            return True
    
    async def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """Periodically clean up old entries to prevent memory leak"""
        async with self._lock:
            current_time = time.time()
            cutoff_time = current_time - max_age_seconds
            
            empty_clients = []
            for client_id, requests in self._requests.items():
                # Remove all requests older than max_age
                while requests and requests[0] < cutoff_time:
                    requests.popleft()
                
                # Mark empty clients for removal
                if not requests:
                    empty_clients.append(client_id)
            
            # Remove empty client entries
            for client_id in empty_clients:
                del self._requests[client_id]


class HybridRateLimiter:
    """
    Hybrid rate limiter that uses Redis when available, falls back to in-memory.
    """
    
    def __init__(self):
        self.redis_available = False
        self.in_memory_limiter = InMemoryRateLimiter()
        self.redis_client = None
        
    async def initialize(self):
        """Initialize rate limiter with Redis if available"""
        if REDIS_AVAILABLE and os.getenv("REDIS_URL"):
            try:
                redis_url = os.getenv("REDIS_URL")
                self.redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
                await FastAPILimiter.init(self.redis_client)
                self.redis_available = True
                print("✅ Redis rate limiter initialized")
                return True
            except Exception as e:
                print(f"⚠️ Redis rate limiter failed, using in-memory fallback: {e}")
                self.redis_available = False
        else:
            print("📝 Using in-memory rate limiter (Redis not configured)")
        
        # Start cleanup task for in-memory limiter
        asyncio.create_task(self._cleanup_task())
        return False
    
    async def _cleanup_task(self):
        """Background task to clean up old in-memory entries"""
        while True:
            await asyncio.sleep(300)  # Clean up every 5 minutes
            await self.in_memory_limiter.cleanup_old_entries()
    
    def create_limiter(self, times: int = 10, seconds: int = 60):
        """
        Create a rate limiter dependency for FastAPI endpoints.
        
        Args:
            times: Maximum number of requests
            seconds: Time window in seconds
        """
        if self.redis_available and RedisRateLimiter:
            # Use Redis rate limiter
            return RedisRateLimiter(times=times, seconds=seconds)
        else:
            # Use in-memory rate limiter
            async def in_memory_dependency(request: Request):
                # Try to extract API key from Authorization header
                auth_header = request.headers.get("Authorization", "")
                api_key = None
                if auth_header.startswith("Bearer "):
                    api_key = auth_header[7:]
                
                await self.in_memory_limiter.check_rate_limit(
                    request, times, seconds, api_key
                )
                return True
            
            return in_memory_dependency
    
    async def close(self):
        """Cleanup resources"""
        if self.redis_available and REDIS_AVAILABLE:
            try:
                await FastAPILimiter.close()
            except Exception as e:
                print(f"Rate limiter cleanup error: {e}")


# Global rate limiter instance
rate_limiter = HybridRateLimiter()


def get_rate_limiter(times: int = 10, seconds: int = 60):
    """
    Get a rate limiter dependency for use in FastAPI endpoints.
    
    Usage:
        @app.post("/api/endpoint", dependencies=[Depends(get_rate_limiter(times=5, seconds=60))])
        async def endpoint():
            ...
    """
    return rate_limiter.create_limiter(times=times, seconds=seconds)
