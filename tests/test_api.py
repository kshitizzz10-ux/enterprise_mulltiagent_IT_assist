import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Enterprise Multi-Agent IT Assistant"
    assert "pipelines" in data


def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_api_chat_action_flow():
    payload = {"query": "My screen is broken, open a ticket."}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["intent"] == "action"
    assert "Pipeline 4" in data["route"]
    assert isinstance(data["response"], dict)
    assert data["response"]["ticket_type"] == "Hardware_Repair"
    assert "execution_log" in data
    assert len(data["execution_log"]) > 0


def test_api_chat_info_flow_with_redaction():
    payload = {"query": "What is the secure corporate VPN server IP?"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["intent"] == "info"
    assert "Pipeline 3" in data["route"]
    # Check that IP is redacted
    assert "192.168.1.100" not in str(data["response"])
    assert "[REDACTED IP]" in str(data["response"])
    assert data["redacted"] is True


def test_api_chat_validation_error():
    payload = {"query": ""}
    response = client.post("/chat", json=payload)
    assert response.status_code == 422
