from unittest.mock import patch, MagicMock

def test_get_people(client):
    with patch("app.routers.people_scraper.get_driver") as mock_driver_cls, \
         patch("app.routers.people_scraper.login_to_linkedin") as mock_login, \
         patch("app.routers.people_scraper.scrape_people_search_logic") as mock_scrape:
        
        mock_driver_cls.return_value.__enter__.return_value = MagicMock()
        mock_login.return_value = True
        mock_scrape.return_value = []

        response = client.get("/scraper/people?search_url=https://linkedin.com/search&email=test@example.com&password=password&max_results=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["people"] == []

def test_download_people_csv(client):
    with patch("app.routers.people_scraper.get_driver") as mock_driver_cls, \
         patch("app.routers.people_scraper.login_to_linkedin") as mock_login, \
         patch("app.routers.people_scraper.scrape_people_search_logic") as mock_scrape, \
         patch("app.routers.people_scraper.generate_csv_stream") as mock_csv:
        
        mock_driver_cls.return_value.__enter__.return_value = MagicMock()
        mock_login.return_value = True
        mock_scrape.return_value = []
        mock_csv.return_value = iter([b"col1\n", b"val1\n"])

        response = client.get("/scraper/people/download?search_url=https://linkedin.com/search&email=test@example.com&password=password")
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "text/csv; charset=utf-8"
        assert "linkedin_people.csv" in response.headers.get("content-disposition", "")
