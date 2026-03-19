import pytest
from app.core.config import settings

def test_analyze_comments(client):
    if not settings.openai_api_key:
        pytest.skip("Skipping real OpenAI analysis test due to missing OPENAI_API_KEY in .env")
    payload = {
        "comments": [
            {
                "author": "Tech User",
                "timestamp": "1h",
                "original_text": "This is an amazing and very helpful post!",
                "cleaned_text": "amazing helpful post",
                "text_length": 41
            }
        ]
    }
    response = client.post("/scraper/analyze", json=payload)
    assert response.status_code == 200
    assert "analysis" in response.json()
