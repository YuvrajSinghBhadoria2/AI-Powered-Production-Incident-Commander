#!/usr/bin/env python3
"""
Quick test script to ingest logs via HTTP API and trigger analysis.
"""

import requests
import json
from datetime import datetime, timedelta

# Load synthetic data
with open("data/synthetic_logs.json", "r") as f:
    logs = json.load(f)

with open("data/synthetic_metrics.json", "r") as f:
    metrics = json.load(f)

print(f"📥 Ingesting {len(logs)} logs via API...")

# Ingest logs one by one
ingested = 0
for log in logs[:50]:  # Ingest first 50 for speed
    try:
        resp = requests.post(
            "http://localhost:8002/ingest/logs/single",
            json=log,
            timeout=5
        )
        if resp.status_code == 201:
            ingested += 1
        else:
            print(f"Failed to ingest log: {resp.status_code} - {resp.text}")
            break
    except Exception as e:
        print(f"Error: {e}")
        break

print(f"✅ Ingested {ingested} logs")

print(f"\n📥 Ingesting {len(metrics)} metrics via API...")
ingested_metrics = 0
for metric in metrics[:50]:  # Ingest first 50 for speed
    try:
        resp = requests.post(
            "http://localhost:8002/ingest/metrics/single",
            json=metric,
            timeout=5
        )
        if resp.status_code == 201:
            ingested_metrics += 1
        else:
            print(f"Failed to ingest metric: {resp.status_code} - {resp.text}")
            break
    except Exception as e:
        print(f"Error: {e}")
        break

print(f"✅ Ingested {ingested_metrics} metrics")

print("\n🔍 Triggering analysis...")
resp = requests.post(
    "http://localhost:8002/analyze/incident",
    json={
        "time_window": "last_1_hour",
        "services": None,
        "severity_threshold": "medium"
    },
    timeout=30
)

if resp.status_code == 200:
    result = resp.json()
    print(f"✅ Analysis complete!")
    print(f"   Incidents detected: {len(result.get('incidents_detected', []))}")
    if result.get('incidents_detected'):
        for inc in result['incidents_detected']:
            print(f"   - {inc['title']} ({inc['severity']})")
else:
    print(f"❌ Analysis failed: {resp.status_code}")
    print(resp.text)

print("\n✨ Done! Now open http://localhost:3000 and click 'Run Analysis'")
