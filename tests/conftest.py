"""
Pytest configuration and shared fixtures for all tests
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, patch
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client(monkeypatch) -> Generator:
    """Create a test client for the FastAPI app"""
    # Mock rate limiter to avoid initialization issues in tests
    from unittest.mock import Mock
    mock_rate_limiter = Mock()
    mock_rate_limiter.create_limiter = Mock(return_value=lambda: None)
    monkeypatch.setattr('main.rate_limiter', mock_rate_limiter)
    monkeypatch.setattr('main.get_rate_limiter', lambda *args, **kwargs: lambda: None)
    
    from main import app
    
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Create an async test client for the FastAPI app"""
    from main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing without API calls"""
    mock_client = Mock()
    mock_client.chat.completions.create = AsyncMock()
    mock_client.embeddings.create = AsyncMock()
    return mock_client


@pytest.fixture
def sample_html_content():
    """Sample HTML content for testing scraper"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Company - AI Solutions</title>
        <meta name="description" content="Leading AI solutions provider">
    </head>
    <body>
        <header>
            <h1>Test Company</h1>
            <nav>
                <a href="/about">About</a>
                <a href="/products">Products</a>
                <a href="/contact">Contact</a>
            </nav>
        </header>
        <main>
            <section class="hero">
                <h2>Revolutionary AI Solutions</h2>
                <p>Transform your business with cutting-edge AI technology</p>
            </section>
            <section class="products">
                <h3>Our Products</h3>
                <ul>
                    <li>AI Analytics Platform</li>
                    <li>Machine Learning Suite</li>
                    <li>Data Processing Tools</li>
                </ul>
            </section>
            <section class="contact">
                <p>Email: contact@testcompany.com</p>
                <p>Phone: +1-555-0123</p>
                <a href="https://twitter.com/testcompany">Twitter</a>
            </section>
        </main>
    </body>
    </html>
    """


@pytest.fixture
def sample_scraped_content():
    """Sample scraped content for testing"""
    from models.pydantic_models import ScrapedContent
    
    return ScrapedContent(
        title="Test Company - AI Solutions",
        meta_description="Leading AI solutions provider",
        headings=["Test Company", "Revolutionary AI Solutions", "Our Products"],
        main_content="Transform your business with cutting-edge AI technology",
        hero_section="Revolutionary AI Solutions - Transform your business",
        products=["AI Analytics Platform", "Machine Learning Suite", "Data Processing Tools"],
        contact_info={
            "emails": ["contact@testcompany.com"],
            "phones": ["+1-555-0123"],
            "social_media": ["https://twitter.com/testcompany"]
        },
        raw_text="TITLE: Test Company - AI Solutions..."
    )


@pytest.fixture
def sample_insights():
    """Sample insights for testing"""
    return {
        "industry": "Artificial Intelligence",
        "company_size": "Medium (51-200)",
        "location": "San Francisco, USA",
        "USP": "Cutting-edge AI solutions for business transformation",
        "products": ["AI Analytics", "ML Suite", "Data Tools"],
        "target_audience": "Enterprise businesses seeking AI transformation",
        "contact_info": {
            "emails": ["contact@testcompany.com"],
            "phones": ["+1-555-0123"],
            "social_media": ["https://twitter.com/testcompany"]
        }
    }


@pytest.fixture
def mock_database_client():
    """Mock database client for testing"""
    mock_client = Mock()
    mock_client.initialize = AsyncMock()
    mock_client.setup_schema = AsyncMock()
    mock_client.get_or_create_website = AsyncMock(return_value=1)
    mock_client.save_insights = AsyncMock()
    mock_client.save_chunks = AsyncMock()
    mock_client.search_similar_chunks = AsyncMock(return_value=["chunk1", "chunk2"])
    mock_client.get_website_insights = AsyncMock()
    mock_client.close = AsyncMock()
    return mock_client


@pytest.fixture
def api_headers():
    """Headers for authenticated API requests"""
    return {
        "Authorization": "Bearer demo-secret-key-for-development",
        "Content-Type": "application/json"
    }


@pytest.fixture
def test_urls():
    """Common test URLs"""
    return {
        "valid": "https://example.com",
        "invalid": "not-a-url",
        "localhost": "http://localhost:8000"
    }


# Environment variable fixtures
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("API_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("ENVIRONMENT", "test")
    # Don't set OPENAI_API_KEY by default to test fallback behavior
