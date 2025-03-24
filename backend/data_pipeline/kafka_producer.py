"""
Kafka Producer for Sensor Data Ingestion
"""

from confluent_kafka import Producer
import json
import logging
import time

class KafkaSensorProducer:
    def __init__(self, bootstrap_servers: str, topic: str):
        self.conf = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': 'airquality-producer'
        }
        self.producer = Producer(self.conf)
        self.topic = topic
        self.logger = logging.getLogger("kafka.producer")

    def delivery_report(self, err, msg):
        """Callback for message delivery status"""
        if err is not None:
            self.logger.error(f"Message delivery failed: {err}")
        else:
            self.logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def produce_sensor_data(self, sensor_data: dict):
        """Produce a sensor reading to Kafka"""
        try:
            self.producer.produce(
                topic=self.topic,
                key=sensor_data['sensor_id'],
                value=json.dumps(sensor_data),
                callback=self.delivery_report
            )
            self.producer.poll(0)
        except Exception as e:
            self.logger.error(f"Production failed: {e}")

    def flush_messages(self):
        """Wait for all messages to be delivered"""
        self.producer.flush()

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    producer = KafkaSensorProducer(
        bootstrap_servers="kafka-broker:9092",
        topic="air-quality-raw"
    )
    
    test_data = {
        "sensor_id": "sensor-01",
        "pm25": 45.6,
        "pm10": 78.9,
        "co2": 1200,
        "temperature": 22.5,
        "humidity": 65,
        "timestamp": time.time()
    }
    
    producer.produce_sensor_data(test_data)
    producer.flush_messages()
