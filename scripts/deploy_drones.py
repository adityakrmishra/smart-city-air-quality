#!/usr/bin/env python3
import json
import random
import time
import argparse
import threading
from typing import Dict, List, Tuple
from kafka import KafkaConsumer, KafkaProducer

class DroneController:
    """Simulates drone fleet deployment based on pollution alerts"""
    
    def __init__(self, config: Dict[str, Any]):
        self.drone_count = config['drone_count']
        self.broker = config['broker']
        self.base_location = config['base_location']
        self.pollution_threshold = config['pollution_threshold']
        
        # Initialize drone fleet
        self.drones = {
            f'drone_{i}': {
                'status': 'available',
                'battery': 100,
                'location': self.base_location,
                'payload': 1000  # ml of dispersant
            }
            for i in range(self.drone_count)
        }
        
        # Kafka setup
        self.consumer = KafkaConsumer(
            'pollution-alerts',
            bootstrap_servers=self.broker,
            auto_offset_reset='latest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        self.producer = KafkaProducer(
            bootstrap_servers=self.broker,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def calculate_optimal_route(self, alert_location: Tuple[float, float]) -> str:
        """Find best available drone for deployment"""
        available_drones = [
            drone_id for drone_id, data in self.drones.items()
            if data['status'] == 'available'
        ]
        
        if not available_drones:
            return None
            
        # Simple distance calculation (Haversine would be better)
        def distance(drone_id):
            lat1, lon1 = self.drones[drone_id]['location']
            lat2, lon2 = alert_location
            return ((lat2-lat1)**2 + (lon2-lon1)**2)**0.5
            
        return min(available_drones, key=distance)

    def simulate_deployment(self, drone_id: str, target: Tuple[float, float]):
        """Simulate drone deployment sequence"""
        try:
            # Update drone status
            self.drones[drone_id]['status'] = 'deploying'
            
            # Simulate travel time (1s = 1km)
            start_lat, start_lon = self.drones[drone_id]['location']
            distance = ((target[0]-start_lat)**2 + (target[1]-start_lon)**2)**0.5
            travel_time = distance * 111 * 2  # 111km/degree * 2x speed factor
            
            print(f"Drone {drone_id} deploying to {target} - ETA: {travel_time:.1f}s")
            time.sleep(travel_time)
            
            # Start dispersal
            self.drones[drone_id]['status'] = 'active'
            dispersal_time = min(
                self.drones[drone_id]['payload'] / 50,  # 50ml/s dispersal rate
                30  # max 30 seconds
            )
            
            print(f"Drone {drone_id} dispersing chemicals for {dispersal_time}s")
            time.sleep(dispersal_time)
            
            # Return to base
            self.drones[drone_id]['status'] = 'returning'
            time.sleep(travel_time)
            
            # Update final state
            self.drones[drone_id].update({
                'status': 'available',
                'location': self.base_location,
                'battery': max(0, self.drones[drone_id]['battery'] - 10),
                'payload': 1000
            })
            
            print(f"Drone {drone_id} mission complete")
            
        except Exception as e:
            print(f"Error in drone {drone_id} mission: {str(e)}")
            self.drones[drone_id]['status'] = 'error'

    def process_alerts(self):
        """Main alert processing loop"""
        print("Listening for pollution alerts...")
        for message in self.consumer:
            alert = message.value
            print(f"Received alert: {json.dumps(alert, indent=2)}")
            
            if alert['severity'] < self.pollution_threshold:
                continue
                
            # Find best drone for deployment
            target = (alert['location']['lat'], alert['location']['lon'])
            drone_id = self.calculate_optimal_route(target)
            
            if drone_id:
                print(f"Dispatching {drone_id} to {alert['location']}")
                # Start deployment in separate thread
                threading.Thread(
                    target=self.simulate_deployment,
                    args=(drone_id, target)
                ).start()
                
                # Send deployment status
                self.producer.send('drone-deployments', {
                    'alert_id': alert['alert_id'],
                    'drone_id': drone_id,
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'status': 'dispatched'
                })
            else:
                print("No available drones for deployment!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Drone Deployment Simulator')
    parser.add_argument('-n', '--drones', type=int, default=3,
                       help='Number of drones in fleet')
    parser.add_argument('-b', '--broker', default='localhost:9092',
                       help='Kafka broker address')
    parser.add_argument('-t', '--threshold', type=float, default=35.0,
                       help='PM2.5 threshold for deployment')
    parser.add_argument('--base-lat', type=float, default=40.7128,
                       help='Base station latitude')
    parser.add_argument('--base-lon', type=float, default=-74.0060,
                       help='Base station longitude')
    
    args = parser.parse_args()
    
    config = {
        'drone_count': args.drones,
        'broker': args.broker,
        'pollution_threshold': args.threshold,
        'base_location': (args.base_lat, args.base_lon)
    }
    
    controller = DroneController(config)
    controller.process_alerts()
