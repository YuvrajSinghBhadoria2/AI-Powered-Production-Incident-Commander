#!/usr/bin/env python3
"""
Ingest synthetic logs and metrics into the AI Incident Commander.
"""

import asyncio
import json
import sys
import os
import httpx

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.db.sqlite_storage import storage


async def ingest_logs():
    """Load and ingest synthetic logs"""
    print("📥 Ingesting synthetic logs...")
    
    from datetime import datetime
    
    with open("data/synthetic_logs.json", "r") as f:
        logs = json.load(f)
    
    for log in logs:
        # Parse timestamp string to datetime
        if isinstance(log.get('timestamp'), str):
            log['timestamp'] = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
        await storage.insert_log(log)
    
    print(f"✅ Ingested {len(logs)} logs")


async def ingest_metrics():
    """Load and ingest synthetic metrics"""
    print("📥 Ingesting synthetic metrics...")
    
    from datetime import datetime
    
    with open("data/synthetic_metrics.json", "r") as f:
        metrics = json.load(f)
    
    for metric in metrics:
        # Parse timestamp string to datetime
        if isinstance(metric.get('timestamp'), str):
            metric['timestamp'] = datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00'))
        await storage.insert_metric(metric)
    
    print(f"✅ Ingested {len(metrics)} metrics")


async def trigger_analysis():
    """Trigger incident analysis via API"""
    print("\n🔍 Triggering incident analysis...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8002/analyze/incident",
                json={
                    "time_window": "last_1_hour",
                    "services": None,
                    "severity_threshold": "medium"
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Analysis complete!")
                print(f"\n📊 Results:")
                print(f"  Incidents detected: {len(result.get('incidents_detected', []))}")
                print(f"  Analysis time: {result.get('analysis_time_ms', 0)}ms")
                
                if result.get('incidents_detected'):
                    for idx, incident in enumerate(result['incidents_detected'], 1):
                        print(f"\n  Incident {idx}:")
                        print(f"    Service: {incident['service']}")
                        print(f"    Severity: {incident['severity']}")
                        print(f"    Title: {incident['title']}")
                
                if result.get('rca_results'):
                    print(f"\n🤖 AI Root Cause Analysis Results ({len(result['rca_results'])}):")
                    for rca in result['rca_results']:
                        print(f"  --- Incident: {rca.get('incident_id')} ---")
                        print(f"  Confidence: {rca.get('confidence_score', 0)*100:.1f}%")
                        print(f"  Root Cause: {rca.get('root_cause', 'N/A')[:200]}...")
                
                return result
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error triggering analysis: {e}")
            return None


async def main():
    print("🚀 Ingesting synthetic data and running analysis...\n")
    
    # Initialize database
    await storage.initialize()
    
    # Ingest data
    await ingest_logs()
    await ingest_metrics()
    
    # Trigger analysis
    result = await trigger_analysis()
    
    if result:
        print("\n✨ Done! Open http://localhost:3000 to see results in the dashboard")
    else:
        print("\n⚠️  Analysis failed. Check backend logs for details.")


if __name__ == "__main__":
    asyncio.run(main())
