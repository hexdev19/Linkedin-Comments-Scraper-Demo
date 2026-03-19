def test_get_comments(client, creds):
    url = f"/scraper/comments?profile_url=https://www.linkedin.com/in/williamhgates&email={creds['email']}&password={creds['password']}&max_comments=1&max_scroll=1"
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "comments" in data

def test_download_comments_csv(client, creds):
    url = f"/scraper/comments/download?profile_url=https://www.linkedin.com/in/williamhgates&email={creds['email']}&password={creds['password']}&max_comments=1&max_scroll=1"
    response = client.get(url)
    assert response.status_code == 200
    assert response.headers.get("content-type") == "text/csv; charset=utf-8"
