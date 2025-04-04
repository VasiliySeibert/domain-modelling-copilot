import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"index.html" in response.data  # Check if the template is rendered

def test_chat_endpoint(client):
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 200
    data = response.get_json()
    assert "response" in data
    assert "history" in data
    assert data["response"]  # Ensure the bot gives a reply