def test_get_group(client, creds):
    url = f"/scraper/group-members?group_url=https://www.linkedin.com/groups/82105/&email={creds['email']}&password={creds['password']}"
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "members" in data

def test_download_group_csv(client, creds):
    url = f"/scraper/group-members/download?group_url=https://www.linkedin.com/groups/82105/&email={creds['email']}&password={creds['password']}"
    response = client.get(url)
    assert response.status_code == 200
    assert response.headers.get("content-type") == "text/csv; charset=utf-8"
