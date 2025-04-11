import pytest
from app import app

@pytest.fixture
def client():
    """Fixture to set up the Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_home_route(client):
    """Test the home route."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Domain Modelling Copilot" in response.data

def test_chat_endpoint_with_valid_message(client):
    """Test the /chat endpoint with a valid message."""
    response = client.post("/chat", json={"message": "Hello, how are you?"})
    assert response.status_code == 200
    assert "response" in response.json
    assert "history" in response.json

def test_chat_endpoint_with_empty_message(client):
    """Test the /chat endpoint with an empty message."""
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 400
    assert response.json["error"] == "Message is required"

def test_process_scenario_with_valid_scenario(client):
    """Test the /process_scenario endpoint with a valid scenario."""
    scenario = "A customer places an order for a product, and the system processes the order."
    response = client.post("/process_scenario", json={"message": scenario})
    assert response.status_code == 200
    assert "plantuml" in response.json
    assert "summary" in response.json
    assert "scenario" in response.json

def test_process_scenario_with_empty_message(client):
    """Test the /process_scenario endpoint with an empty message."""
    response = client.post("/process_scenario", json={"message": ""})
    assert response.status_code == 400
    assert response.json["error"] == "Scenario text is required"