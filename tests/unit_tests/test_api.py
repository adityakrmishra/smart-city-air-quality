import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database.timescale_schema import get_test_db
from sqlalchemy.orm import sessionmaker

# Fixtures
@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)

@pytest.fixture(scope="module")
def test_db():
    engine = get_test_db()
    Session = sessionmaker(bind=engine)
    return Session()

def test_ingest_sensor_data_valid(test_client, test_db):
    payload = {
        "sensor_id": "sensor-01",
        "pm25": 35.6,
        "pm10": 58.9,
        "co2": 1200,
        "temperature": 22.5,
        "humidity": 65,
        "timestamp": "2023-07-15T12:00:00Z"
    }
    response = test_client.post("/api/sensor-data", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_ingest_sensor_data_invalid(test_client):
    payload = {
        "sensor_id": "sensor-01",
        "pm25": "invalid",  # Wrong type
        "timestamp": "invalid-date"
    }
    response = test_client.post("/api/sensor-data", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(e["loc"] == ["body", "pm25"] for e in errors)

def test_historical_data_query(test_client, test_db):
    params = {
        "sensor_id": "sensor-01",
        "start": "2023-07-15T00:00:00Z",
        "end": "2023-07-15T23:59:59Z",
        "resolution": "1h"
    }
    response = test_client.get("/api/historical", params=params)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 24
    assert all("pm25" in item for item in data)

@pytest.mark.asyncio
async def test_websocket_realtime(test_client):
    with test_client.websocket_connect("/ws/realtime") as websocket:
        websocket.send_text("subscribe:sensor-01")
        response = websocket.receive_text()
        assert "ack" in response
