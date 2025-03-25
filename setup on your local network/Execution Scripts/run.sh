#!/bin/bash

# Start core services
docker-compose -f devops/docker-compose.db.yml up -d
docker-compose -f devops/docker-compose.kafka.yml up -d

# Initialize databases
python backend/database/init_timescale.py
influx setup -u admin -p securepass -o airquality -b airquality -f

# Start API server
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 &

# Start sensor simulator
python hardware/sensors/emulator.py --count 50 &

# Start model orchestrator
python backend/orchestrator/model_manager.py &

# Start drone controller
python scripts/deploy_drones.py --drones 5
