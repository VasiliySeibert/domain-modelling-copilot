import pytest
from app import app

@pytest.fixture
def client():
    """Set up Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

# Test the home route
def test_home_route(client):
    """Test the home route."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Domain Modelling Copilot" in response.data

# Test the /chat endpoint with a valid general message
def test_chat_endpoint_with_valid_general_message(client):
    """Test the /chat endpoint with a valid general message."""
    with client.session_transaction() as session:
        session["user_name"] = "John Doe"

    response = client.post("/chat", json={"message": "What is domain modeling?"})
    assert response.status_code == 200
    assert "response" in response.json

# Test the /chat endpoint with a valid scenario message
def test_chat_endpoint_with_valid_scenario_message(client):
    """Test the /chat endpoint with a valid scenario message."""
    with client.session_transaction() as session:
        session["user_name"] = "John Doe"

    response = client.post("/chat", json={"message": "A customer places an order for a product."})
    assert response.status_code == 200
    assert "scenario" in response.json
    assert "summary" in response.json

# Test the /chat endpoint with an empty message
def test_chat_endpoint_with_empty_message(client):
    """Test the /chat endpoint with an empty message."""
    with client.session_transaction() as session:
        session["user_name"] = "John Doe"

    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 400
    assert response.json["error"] == "Message is required"

# Test the /submit_name endpoint with a valid name
def test_submit_name_with_valid_name(client):
    """Test the /submit_name endpoint with a valid name."""
    response = client.post("/submit_name", json={"name": "John Doe"})
    assert response.status_code == 200
    assert response.json["message"] == "Name saved successfully!"

# Test the /submit_name endpoint with an empty name
def test_submit_name_with_empty_name(client):
    """Test the /submit_name endpoint with an empty name."""
    response = client.post("/submit_name", json={"name": ""})
    assert response.status_code == 400
    assert response.json["error"] == "Name is required"

# Test the /generate_uml endpoint with valid scenario text
def test_generate_uml_with_valid_scenario(client):
    """Test the /generate_uml endpoint with valid scenario text."""
    scenario_text = "A customer places an order for a product, and the system processes the order."
    response = client.post("/generate_uml", json={"scenarioText": scenario_text})
    assert response.status_code == 200
    assert "plantuml" in response.json

# Test the /generate_uml endpoint with empty scenario text
def test_generate_uml_with_empty_scenario(client):
    """Test the /generate_uml endpoint with empty scenario text."""
    response = client.post("/generate_uml", json={"scenarioText": ""})
    assert response.status_code == 400
    assert response.json["error"] == "Scenario text is required"

# Test the /generate_summary endpoint with valid detailed description
def test_generate_summary_with_valid_description(client):
    """Test the /generate_summary endpoint with valid detailed description."""
    detailed_description = "A customer places an order for a product, and the system processes the order."
    response = client.post("/generate_summary", json={"detailed_description": detailed_description})
    assert response.status_code == 200
    assert "summary" in response.json

# Test the /generate_summary endpoint with empty detailed description
def test_generate_summary_with_empty_description(client):
    """Test the /generate_summary endpoint with empty detailed description."""
    response = client.post("/generate_summary", json={"detailed_description": ""})
    assert response.status_code == 400
    assert response.json["error"] == "Detailed description is required"

# Test the /chat endpoint when user name is not set
def test_chat_without_user_name(client):
    """Test the /chat endpoint when user name is not set."""
    response = client.post("/chat", json={"message": "What is domain modeling?"})
    assert response.status_code == 400
    assert response.json["error"] == "User name is not set. Please submit your name first."

# Test the /chat endpoint with invalid classification
def test_chat_with_invalid_classification(client, monkeypatch):
    """Test the /chat endpoint with invalid classification."""
    def mock_classify_input(_):
        return "invalid"
    monkeypatch.setattr("app.classify_input", mock_classify_input)

    with client.session_transaction() as session:
        session["user_name"] = "John Doe"

    response = client.post("/chat", json={"message": "What is domain modeling?"})
    assert response.status_code == 400
    assert response.json["error"] == "Unable to classify the input. Please rephrase your query."