def test_login_success(client, creds):
    response = client.post("/auth/login", json={"email": creds["email"], "password": creds["password"]})
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Successfully logged into LinkedIn"}


