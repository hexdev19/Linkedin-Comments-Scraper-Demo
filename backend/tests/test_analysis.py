from unittest.mock import patch

def test_analyze_comments(client):
    with patch("app.routers.analysis.analyze_comments_logic") as mock_analyze:
        mock_analyze.return_value = {"sentiment": "positive"}

        response = client.post("/scraper/analyze", json={"comments": ["Great post!", "I agree"]})
        
        assert response.status_code == 200
        assert response.json() == {"analysis": {"sentiment": "positive"}}

def test_analyze_comments_failure(client):
    with patch("app.routers.analysis.analyze_comments_logic") as mock_analyze:
        mock_analyze.side_effect = Exception("Test error")

        response = client.post("/scraper/analyze", json={"comments": []})
        
        assert response.status_code == 500
        assert "Test error" in response.json()["detail"]
