def test_get_company(client, creds):
    url = f"/scraper/companies?keywords=Microsoft&email={creds['email']}&password={creds['password']}&max_pages=1"
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data

def test_download_company_csv(client, creds):
    url = f"/scraper/companies/download?keywords=Microsoft&email={creds['email']}&password={creds['password']}&max_pages=1"
    response = client.get(url)
    assert response.status_code == 200
    assert response.headers.get("content-type") == "text/csv; charset=utf-8"
