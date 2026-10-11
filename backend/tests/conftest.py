import os

os.environ.setdefault("SEC_CONTACT_EMAIL", "test@example.com")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")

import pytest
from fastapi.testclient import TestClient

from app.caching.memory import InMemoryTTLCache
from app.deps import get_cache
from app.main import app


@pytest.fixture
def client():
    app.dependency_overrides[get_cache] = lambda: InMemoryTTLCache()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
