import requests_mock
from backend.api.traffic_integration.traffic_control import TrafficController

def test_traffic_control_flow():
    with requests_mock.Mocker() as m:
        # Mock Traffic API
        m.post("https://traffic-api.cityservice.com/v1/intersections/A12/control",
               json={"status": "success"})
        
        controller = TrafficController(api_key="test-key")
        sensor_data = {
            "pm25": 80,  # Above threshold
            "co2": 1500,
            "temperature": 25
        }
        adjustment = controller.calculate_optimal_flow(sensor_data)
        result = controller.apply_traffic_changes(adjustment)
        
        assert result is True
        assert m.call_count == 1
        assert "green_extension" in m.request_history[0].json()
