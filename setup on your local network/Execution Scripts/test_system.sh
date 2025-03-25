#!/bin/bash

# Test API endpoints
curl -X GET http://localhost:8000/api/health | jq
curl -X POST http://localhost:8000/api/simulate-alert | jq

# Test Kafka topics
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic raw-sensor-data --max-messages 5

# Validate blockchain operations
peer chaincode query -C mychannel -n sensorcc \
  -c '{"Args":["GetData","sensor1","2023-01-01","2023-12-31"]}'
