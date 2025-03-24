-- TimescaleDB Schema for Sensor Data
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE sensor_readings (
    timestamp TIMESTAMPTZ NOT NULL,
    sensor_id TEXT NOT NULL,
    pm25 DOUBLE PRECISION,
    pm10 DOUBLE PRECISION,
    co2 INTEGER,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION
);

SELECT create_hypertable('sensor_readings', 'timestamp');

CREATE INDEX idx_sensor_time ON sensor_readings (sensor_id, timestamp DESC);

-- Materialized view for daily aggregates
CREATE MATERIALIZED VIEW daily_aggregates
WITH (timescaledb.continuous) AS
SELECT
    sensor_id,
    time_bucket('1 day', timestamp) AS bucket,
    AVG(pm25) AS avg_pm25,
    MAX(pm10) AS max_pm10,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY co2) AS p95_co2
FROM sensor_readings
GROUP BY sensor_id, bucket;
