"""
FastAPI Server for Sensor Data & Traffic Control
"""

from fastapi import FastAPI, WebSocket, HTTPException
from pydantic import BaseModel
from datetime import datetime
import logging
import psycopg2
import uvicorn
from typing import List, Optional
import json

# Configuration
app = FastAPI(title="Smart City API", version="1.0.0")
logger = logging.getLogger("uvicorn.error")

# Database Configuration
DB_CONFIG = {
    "dbname": "airquality",
    "user": "admin",
    "password": "securepass",
    "host": "timescale-db",
    "port": "5432"
}

class SensorData(BaseModel):
    sensor_id: str
    pm25: float
    pm10: float
    co2: float
    temperature: float
    humidity: float
    timestamp: datetime

class TrafficRequest(BaseModel):
    intersection_id: str
    desired_state: str  # "normal", "reduce_congestion"
    duration_minutes: int

@app.on_event("startup")
async def startup_db():
    try:
        app.state.conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connected to TimescaleDB")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

@app.post("/api/sensor-data")
async def ingest_sensor_data(data: SensorData):
    """Endpoint for sensor data ingestion"""
    try:
        cur = app.state.conn.cursor()
        query = """
            INSERT INTO sensor_readings 
            (sensor_id, pm25, pm10, co2, temperature, humidity, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (
            data.sensor_id, data.pm25, data.pm10, 
            data.co2, data.temperature, data.humidity, 
            data.timestamp
        ))
        app.state.conn.commit()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"DB write failed: {e}")
        raise HTTPException(status_code=500, detail="Data ingestion failed")

@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    """WebSocket for real-time dashboard updates"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Process real-time commands here
            await websocket.send_text(json.dumps({
                "status": "ack",
                "timestamp": datetime.utcnow().isoformat()
            }))
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

@app.get("/api/historical")
async def get_historical_data(
    sensor_id: str, 
    start: datetime, 
    end: datetime,
    resolution: str = "1h"
):
    """Fetch time-bucketed historical data"""
    try:
        cur = app.state.conn.cursor()
        query = """
            SELECT time_bucket(%s, timestamp) AS bucket,
                   AVG(pm25) as avg_pm25,
                   MAX(pm10) as max_pm10
            FROM sensor_readings
            WHERE sensor_id = %s AND timestamp BETWEEN %s AND %s
            GROUP BY bucket
            ORDER BY bucket
        """
        cur.execute(query, (resolution, sensor_id, start, end))
        results = cur.fetchall()
        return [{
            "timestamp": row[0].isoformat(),
            "pm25": row[1],
            "pm10": row[2]
        } for row in results]
    except Exception as e:
        logger.error(f"Historical query failed: {e}")
        raise HTTPException(status_code=500, detail="Query failed")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
