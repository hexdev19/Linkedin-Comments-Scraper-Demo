from unittest.mock import patch, MagicMock

def test_get_comments(client):
    with patch("app.routers.comments_scraper.get_driver") as mock_driver_cls, \
         patch("app.routers.comments_scraper.login_to_linkedin") as mock_login, \
         patch("app.routers.comments_scraper.scrape_comments_logic") as mock_scrape:
        
        mock_driver_cls.return_value.__enter__.return_value = MagicMock()
        mock_login.return_value = True
        mock_scrape.return_value = []

        response = client.get("/scraper/comments?profile_url=https://linkedin.com/in/test&email=test@example.com&password=password&max_comments=10&max_scroll=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["comments_scraped"] == 0
        assert data["comments"] == []

def test_download_comments_csv(client):
    with patch("app.routers.comments_scraper.get_driver") as mock_driver_cls, \
         patch("app.routers.comments_scraper.login_to_linkedin") as mock_login, \
         patch("app.routers.comments_scraper.scrape_comments_logic") as mock_scrape, \
         patch("app.routers.comments_scraper.generate_csv_stream") as mock_csv:
        
        mock_driver_cls.return_value.__enter__.return_value = MagicMock()
        mock_login.return_value = True
        mock_scrape.return_value = []
        mock_csv.return_value = iter([b"col1,col2\n", b"val1,val2\n"])

        response = client.get("/scraper/comments/download?profile_url=https://linkedin.com/in/test&email=test@example.com&password=password")
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "text/csv; charset=utf-8"
        assert "linkedin_comments.csv" in response.headers.get("content-disposition", "")
