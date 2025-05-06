import io
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def get_auth_headers():
    response = client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_upload_csv():
    headers = get_auth_headers()
    csv_content = b"review_text,rating\nGreat product!,5\nNot good,2"
    files = {
        "file": ("reviews.csv", io.BytesIO(csv_content), "text/csv")
    }
    response = client.post("/api/upload", headers=headers, files=files)
    assert response.status_code == 200
    assert "reviews" in response.json()

def test_scrape_twitter():
    headers = get_auth_headers()
    data = {
        "query": "product review",
        "limit": 10
    }
    response = client.post("/api/scrape/twitter", headers=headers, json=data)
    assert response.status_code == 200
    assert "reviews" in response.json()

def test_analyze_sentiment():
    headers = get_auth_headers()
    data = {
        "reviews": [
            {"text": "Great product!", "rating": 5},
            {"text": "Not good", "rating": 2}
        ]
    }
    response = client.post("/api/analyze", headers=headers, json=data)
    assert response.status_code == 200
    assert "analysis" in response.json()

def test_generate_report():
    headers = get_auth_headers()
    data = {
        "analysis_results": {
            "sentiment_scores": [0.8, 0.2],
            "average_rating": 3.5,
            "review_count": 2
        }
    }
    response = client.post("/api/report", headers=headers, json=data)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf" 