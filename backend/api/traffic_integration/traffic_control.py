"""
Traffic Light Control Integration Module
"""

import requests
import logging
from typing import Dict
from datetime import timedelta
from .main import SensorData  # Reuse data model

class TrafficController:
    def __init__(self, api_key: str):
        self.base_url = "https://traffic-api.cityservice.com/v1"
        self.headers = {"X-API-Key": api_key}
        self.current_states: Dict[str, str] = {}

    def calculate_optimal_flow(self, sensor_data: SensorData) -> dict:
        """Calculate traffic light timing adjustments"""
        adjustment = {"intersection_id": "A12", "phase_changes": []}
        
        # Example congestion reduction logic
        if sensor_data.pm25 > 75:
            adjustment["phase_changes"].extend([
                {"light_id": "N-S", "green_extension": 30},
                {"light_id": "E-W", "red_extension": 45}
            ])
        elif sensor_data.co2 > 1200:
            adjustment["phase_changes"].append(
                {"light_id": "ALL", "cycle_time": 120}
            )
            
        return adjustment

    def apply_traffic_changes(self, adjustment: dict) -> bool:
        """Send commands to traffic API"""
        try:
            response = requests.post(
                f"{self.base_url}/intersections/{adjustment['intersection_id']}/control",
                json=adjustment,
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            self.current_states[adjustment["intersection_id"]] = "modified"
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Traffic API failed: {e}")
            return False

    def revert_to_normal(self, intersection_id: str):
        """Reset traffic lights to default state"""
        try:
            response = requests.delete(
                f"{self.base_url}/intersections/{intersection_id}/control",
                headers=self.headers
            )
            if response.status_code == 200:
                self.current_states[intersection_id] = "normal"
            return response.ok
        except requests.exceptions.RequestException as e:
            logging.error(f"Traffic revert failed: {e}")
            return False
