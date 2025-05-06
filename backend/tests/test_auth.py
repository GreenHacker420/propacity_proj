from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login_success():
    response = client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_wrong_password():
    response = client.post(
        "/auth/token",
        data={"username": "admin", "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_get_user_me():
    # First login to get token
    login_response = client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin123"},
    )
    token = login_response.json()["access_token"]
    
    # Use token to get user info
    response = client.get(
        "/auth/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "admin"

def test_get_user_me_no_token():
    response = client.get("/auth/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated" 