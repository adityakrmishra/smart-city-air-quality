import pytest
from confluent_kafka import Producer, Consumer
from backend.data_pipeline.kafka_producer import KafkaSensorProducer
from backend.api.main import app
from sqlalchemy import text
import time

@pytest.fixture(scope="module")
def kafka_setup():
    producer = Producer({'bootstrap.servers': 'localhost:9092'})
    consumer = Consumer({
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'integration-test',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe(['air-quality-raw'])
    return producer, consumer

def test_full_pipeline(kafka_setup, test_db):
    # 1. Produce test message
    producer, consumer = kafka_setup
    test_msg = {
        'sensor_id': 'integration-sensor',
        'pm25': 45.6,
        'pm10': 78.9,
        'co2': 1200,
        'temperature': 22.5,
        'humidity': 65,
        'timestamp': time.time()
    }
    producer.produce('air-quality-raw', value=json.dumps(test_msg))
    producer.flush()

    # 2. Consume from Kafka
    msg = consumer.poll(10.0)
    assert msg is not None
    assert json.loads(msg.value()) == test_msg

    # 3. Verify database insertion
    time.sleep(5)  # Allow pipeline processing
    with test_db() as session:
        result = session.execute(text("""
            SELECT * FROM sensor_readings
            WHERE sensor_id = 'integration-sensor'
        """))
        assert result.rowcount == 1
        row = result.fetchone()
        assert row.pm25 == 45.6

    # 4. Verify API endpoint
    test_client = TestClient(app)
    response = test_client.get(f"/api/historical?sensor_id=integration-sensor")
    assert response.status_code == 200
    assert len(response.json()) >= 1
