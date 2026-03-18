from unittest.mock import patch, MagicMock

def test_login_success(client):
    with patch("app.routers.auth.get_driver") as mock_driver_cls, \
         patch("app.routers.auth.login_to_linkedin") as mock_login:
        
        mock_driver_cls.return_value.__enter__.return_value = MagicMock()
        mock_login.return_value = True

        response = client.post("/auth/login", json={"email": "test@example.com", "password": "password"})
        
        assert response.status_code == 200
        assert response.json() == {"success": True, "message": "Successfully logged into LinkedIn"}

def test_login_failure(client):
    with patch("app.routers.auth.get_driver") as mock_driver_cls, \
         patch("app.routers.auth.login_to_linkedin") as mock_login:
        
        mock_driver_cls.return_value.__enter__.return_value = MagicMock()
        mock_login.return_value = False

        response = client.post("/auth/login", json={"email": "test@example.com", "password": "password"})
        
        assert response.status_code == 200
        assert response.json() == {"success": False, "message": "Login failed"}
