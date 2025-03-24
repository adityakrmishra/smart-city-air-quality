"""
LoRaWAN Configuration and Data Forwarding
Handles sensor data reception and cloud forwarding
"""

import serial
import json
import requests
from datetime import datetime
import logging
import sys

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class LoraConfig:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )
        self.gateway_id = "GW-01"
        self.backend_url = "https://api.yourbackend.com/ingest"
        
        # Sensor ID mapping
        self.sensor_map = {
            "00:0A:E6:12:34:56": "street-a12",
            "00:0A:E6:12:34:57": "park-b24"
        }

    def parse_packet(self, raw_data):
        """Parse raw LoRa payload into structured format"""
        try:
            parts = raw_data.decode().strip().split(',')
            if len(parts) != 5:
                raise ValueError("Invalid packet format")
                
            return {
                "pm25": float(parts[0]),
                "pm10": float(parts[1]),
                "co2": float(parts[2]),
                "temp": float(parts[3]),
                "humidity": float(parts[4]),
                "timestamp": datetime.utcnow().isoformat(),
                "gateway": self.gateway_id
            }
        except Exception as e:
            logging.error(f"Parsing failed: {str(e)}")
            return None

    def forward_to_backend(self, data, sensor_id):
        """Send processed data to cloud backend"""
        payload = {
            **data,
            "location": self.sensor_map.get(sensor_id, "unknown"),
            "sensor_id": sensor_id
        }
        
        try:
            response = requests.post(
                self.backend_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            response.raise_for_status()
            logging.info(f"Data forwarded: {payload}")
        except Exception as e:
            logging.error(f"Backend comms failed: {str(e)}")

    def listen(self):
        """Main listening loop"""
        logging.info(f"Starting LoRa listener on {self.ser.port}")
        
        while True:
            try:
                if self.ser.in_waiting > 0:
                    raw = self.ser.readline()
                    sensor_id = self.extract_sensor_id(raw)  # Implement MAC extraction
                    parsed = self.parse_packet(raw)
                    
                    if parsed:
                        self.forward_to_backend(parsed, sensor_id)
                        
            except serial.SerialException as se:
                logging.error(f"Serial error: {str(se)}")
                sys.exit(1)
            except KeyboardInterrupt:
                logging.info("Shutting down listener")
                self.ser.close()
                sys.exit(0)

if __name__ == "__main__":
    lora = LoraConfig(port='/dev/ttyAMA0')
    lora.listen()
