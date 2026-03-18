from unittest.mock import patch, MagicMock

def test_get_company(client):
    with patch("app.routers.company_scraper.get_driver") as mock_driver_cls, \
         patch("app.routers.company_scraper.login_to_linkedin") as mock_login, \
         patch("app.routers.company_scraper.scrape_companies_logic") as mock_scrape:
        
        mock_driver_cls.return_value.__enter__.return_value = MagicMock()
        mock_login.return_value = True
        mock_scrape.return_value = []

        response = client.get("/scraper/companies?keywords=test&email=test@example.com&password=password&max_pages=1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["companies_scraped"] == 0
        assert data["data"] == []

def test_download_company_csv(client):
    with patch("app.routers.company_scraper.get_driver") as mock_driver_cls, \
         patch("app.routers.company_scraper.login_to_linkedin") as mock_login, \
         patch("app.routers.company_scraper.scrape_companies_logic") as mock_scrape, \
         patch("app.routers.company_scraper.generate_csv_stream") as mock_csv:
        
        mock_driver_cls.return_value.__enter__.return_value = MagicMock()
        mock_login.return_value = True
        mock_scrape.return_value = []
        mock_csv.return_value = iter([b"col1\n", b"val1\n"])

        response = client.get("/scraper/companies/download?keywords=test&email=test@example.com&password=password")
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "text/csv; charset=utf-8"
        assert "linkedin_companies_test.csv" in response.headers.get("content-disposition", "")
