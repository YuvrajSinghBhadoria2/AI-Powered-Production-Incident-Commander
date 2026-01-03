#!/bin/bash

# AI Incident Commander - OTel Integration Test Flow
# This script runs the full cycle: Generate -> Ingest -> Analyze

echo "--------------------------------------------------"
echo "🚀 Step 1: Generating OTel-style incident data..."
echo "--------------------------------------------------"
python3 scripts/generate_otel_data.py

echo -e "\n--------------------------------------------------"
echo "📡 Step 2: Ingesting data into Backend (localhost:8000)..."
echo "--------------------------------------------------"

# Ingest Checkout Failure Logs
echo "[Checkout Service] Ingesting logs..."
curl -s -X POST http://localhost:8000/ingest/otel \
     -H "Content-Type: application/json" \
     -d @data/otel_checkout_failure.json | jq .status

# Ingest Product Catalog Failure Logs
echo "[Product Catalog] Ingesting logs..."
curl -s -X POST http://localhost:8000/ingest/otel \
     -H "Content-Type: application/json" \
     -d @data/otel_catalog_failure.json | jq .status

# Ingest Recommendation Latency Metrics
echo "[Recommendation Service] Ingesting metrics..."
curl -s -X POST http://localhost:8000/ingest/otel \
     -H "Content-Type: application/json" \
     -d @data/otel_reco_latency.json | jq .status

echo -e "\n--------------------------------------------------"
echo "🧠 Step 3: Triggering AI Incident Analysis..."
echo "--------------------------------------------------"
echo "Waiting for LLM to reconstruct the timeline (this may take 10-15s)..."

curl -s -X POST http://localhost:8000/analyze/incident \
     -H "Content-Type: application/json" \
     -d '{"time_window": "last_30_min"}' | jq '.rca_results[] | {incident_id, root_cause, confidence_score}'

echo -e "\n--------------------------------------------------"
echo "✅ Test Flow Complete!"
echo "Check the Frontend Dashboard at http://localhost:3000 to see the timeline."
echo "--------------------------------------------------"
