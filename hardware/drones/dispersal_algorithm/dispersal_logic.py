import numpy as np
from typing import Tuple

class PollutionDispersal:
    def __init__(self, city_map_resolution: float = 0.0001):
        self.city_map = np.zeros((100, 100))  # 100x100 grid
        self.resolution = city_map_resolution  # Degrees per grid cell
        
    def update_pollution_map(self, sensor_data: dict):
        """Update pollution map with sensor readings"""
        for location, value in sensor_data.items():
            x, y = self._location_to_grid(location)
            self.city_map[x, y] = value
            
    def find_hotspot(self, current_position: Tuple[float, float]) -> Tuple[float, float]:
        """Find most critical pollution hotspot near drone"""
        x, y = self._location_to_grid(current_position)
        
        # Search 10x10 area around current position
        search_radius = 5
        min_x = max(0, x - search_radius)
        max_x = min(99, x + search_radius)
        min_y = max(0, y - search_radius)
        max_y = min(99, y + search_radius)
        
        region = self.city_map[min_x:max_x, min_y:max_y]
        max_index = np.unravel_index(region.argmax(), region.shape)
        
        return self._grid_to_location(
            min_x + max_index[0], 
            min_y + max_index[1]
        )

    def calculate_dispersal_pattern(self, pollution_level: float) -> dict:
        """Calculate dispersal parameters based on pollution level"""
        return {
            'rate': min(pollution_level * 0.5, 100),  # ml/s
            'duration': min(pollution_level * 0.2, 30),  # seconds
            'chemical_mix': {
                'water': 0.7,
                'hydrogen_peroxide': 0.2,
                'surfactant': 0.1
            }
        }

    def _location_to_grid(self, location: Tuple[float, float]) -> Tuple[int, int]:
        lat, lon = location
        return (
            int((lat - 40.0) / self.resolution),  # Example base latitude
            int((lon - -75.0) / self.resolution)   # Example base longitude
        )

    def _grid_to_location(self, x: int, y: int) -> Tuple[float, float]:
        return (
            40.0 + x * self.resolution,
            -75.0 + y * self.resolution
        )
