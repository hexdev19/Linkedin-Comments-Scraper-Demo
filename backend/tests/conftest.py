import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="module")
def creds():
    if not settings.linkedin_email or not settings.linkedin_password:
        pytest.fail(f"Error: Missing LINKEDIN_EMAIL or LINKEDIN_PASSWORD. Searched exactly at {env_path}")
    return {"email": settings.linkedin_email, "password": settings.linkedin_password}
