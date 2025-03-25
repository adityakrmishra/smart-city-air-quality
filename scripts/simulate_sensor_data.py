#!/usr/bin/env python3
import random
import time
import json
import argparse
from datetime import datetime
from kafka import KafkaProducer
from typing import Dict, Any

class SensorSimulator:
    """Simulates IoT air quality sensors and sends data to Kafka"""
    
    def __init__(self, config: Dict[str, Any]):
        self.sensor_count = config['sensor_count']
        self.interval = config['interval']
        self.broker = config['broker']
        self.running = True
        self.producer = KafkaProducer(
            bootstrap_servers=self.broker,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all'
        )
        
        # Sensor location boundaries (example: New York City area)
        self.min_lat = 40.4774
        self.max_lat = 40.9176
        self.min_lon = -74.2591
        self.max_lon = -73.7004
        
        # Initialize sensor states
        self.sensors = {
            f'sensor_{i}': {
                'base_pm25': random.uniform(5, 25),
                'base_pm10': random.uniform(10, 40),
                'base_co2': random.uniform(400, 600),
                'lat': random.uniform(self.min_lat, self.max_lat),
                'lon': random.uniform(self.min_lon, self.max_lon)
            }
            for i in range(self.sensor_count)
        }

    def generate_sensor_data(self, sensor_id: str) -> Dict[str, Any]:
        """Generate realistic sensor readings with occasional spikes"""
        sensor = self.sensors[sensor_id]
        
        # Simulate normal fluctuation
        pm25 = sensor['base_pm25'] * random.uniform(0.9, 1.1)
        pm10 = sensor['base_pm10'] * random.uniform(0.9, 1.15)
        co2 = sensor['base_co2'] * random.uniform(0.95, 1.05)

        # 15% chance of pollution spike
        if random.random() < 0.15:
            pm25 *= random.uniform(2, 8)
            pm10 *= random.uniform(1.5, 4)
            co2 *= random.uniform(1.2, 3)
            
        return {
            'sensor_id': sensor_id,
            'timestamp': datetime.utcnow().isoformat(),
            'location': {
                'lat': round(sensor['lat'], 6),
                'lon': round(sensor['lon'], 6)
            },
            'readings': {
                'pm2_5': round(max(0, pm25), 1),
                'pm10': round(max(0, pm10), 1),
                'co2': round(max(300, co2), 0)
            },
            'status': {
                'battery': random.randint(75, 100),
                'signal': random.randint(1, 5)
            }
        }

    def run(self):
        """Main simulation loop"""
        try:
            while self.running:
                for sensor_id in self.sensors:
                    data = self.generate_sensor_data(sensor_id)
                    self.producer.send('raw-sensor-data', data)
                    print(f"Sent data: {json.dumps(data, indent=2)}")
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\nSimulation stopped by user")
        finally:
            self.producer.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Air Quality Sensor Simulator')
    parser.add_argument('-n', '--sensors', type=int, default=5,
                       help='Number of sensors to simulate')
    parser.add_argument('-i', '--interval', type=float, default=15.0,
                       help='Seconds between sensor readings')
    parser.add_argument('-b', '--broker', default='localhost:9092',
                       help='Kafka broker address')
    parser.add_argument('--infinite', action='store_true',
                       help='Run indefinitely')
    
    args = parser.parse_args()
    
    config = {
        'sensor_count': args.sensors,
        'interval': args.interval,
        'broker': args.broker
    }
    
    simulator = SensorSimulator(config)
    print(f"Starting simulation with {args.sensors} sensors...")
    simulator.run()
