#!/usr/bin/env python3
"""
Generate synthetic logs and metrics for testing the AI Incident Commander.
Creates realistic incident scenarios:
- Memory leaks
- Database connection exhaustion
- API latency spikes
- Network timeouts
"""

import random
import json
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


SERVICES = ["payment-api", "user-service", "auth-service", "gateway", "database", "cache"]

LOG_LEVELS = ["debug", "info", "warning", "error", "critical"]

ERROR_PATTERNS = {
    "db_connection": [
        "Database connection timeout after 30s",
        "Connection pool exhausted: max 100 connections reached",
        "Failed to acquire database connection",
        "Connection refused: database unavailable",
        "Too many connections to database"
    ],
    "memory": [
        "OutOfMemoryError: Java heap space",
        "Memory allocation failed",
        "GC overhead limit exceeded",
        "Cannot allocate memory",
        "Memory usage at 95%"
    ],
    "api_latency": [
        "Request timeout after 5000ms",
        "Slow query detected: 4.8s",
        "API response time exceeded threshold",
        "Downstream service timeout",
        "Circuit breaker opened due to failures"
    ],
    "network": [
        "Connection reset by peer",
        "Network unreachable",
        "Packet loss detected: 15%",
        "DNS resolution failed",
        "SSL handshake timeout"
    ]
}


def generate_incident_scenario(incident_type="db_connection", duration_minutes=30):
    """Generate a complete incident scenario with logs and metrics"""
    
    start_time = datetime.now() - timedelta(minutes=duration_minutes)
    logs = []
    metrics = []
    
    if incident_type == "db_connection":
        # Simulate database connection pool exhaustion
        service = "payment-api"
        
        # Normal operation (first 10 minutes)
        for i in range(10):
            timestamp = start_time + timedelta(minutes=i)
            
            # Normal logs
            logs.append({
                "timestamp": timestamp.isoformat(),
                "service": service,
                "level": "info",
                "message": "Processing payment request",
                "trace_id": f"trace_{random.randint(1000, 9999)}"
            })
            
            # Normal metrics
            metrics.append({
                "timestamp": timestamp.isoformat(),
                "service": service,
                "metric_name": "db_connections_active",
                "value": random.uniform(40, 60),
                "unit": "count"
            })
            
            metrics.append({
                "timestamp": timestamp.isoformat(),
                "service": service,
                "metric_name": "api_latency_ms",
                "value": random.uniform(150, 250),
                "unit": "milliseconds"
            })
        
        # Incident starts (connections start climbing)
        for i in range(10, 20):
            timestamp = start_time + timedelta(minutes=i)
            
            # Increasing error rate
            if random.random() < 0.3:
                logs.append({
                    "timestamp": timestamp.isoformat(),
                    "service": service,
                    "level": "error",
                    "message": random.choice(ERROR_PATTERNS["db_connection"]),
                    "trace_id": f"trace_{random.randint(1000, 9999)}"
                })
            
            # Connections climbing
            metrics.append({
                "timestamp": timestamp.isoformat(),
                "service": service,
                "metric_name": "db_connections_active",
                "value": 60 + (i - 10) * 4,  # Climbing to 100
                "unit": "count"
            })
            
            # Latency increasing
            metrics.append({
                "timestamp": timestamp.isoformat(),
                "service": service,
                "metric_name": "api_latency_ms",
                "value": 250 + (i - 10) * 200,  # Climbing to 2250ms
                "unit": "milliseconds"
            })
        
        # Peak incident (connections at max)
        for i in range(20, 25):
            timestamp = start_time + timedelta(minutes=i)
            
            # High error rate
            for _ in range(5):
                logs.append({
                    "timestamp": timestamp.isoformat(),
                    "service": service,
                    "level": "critical" if random.random() < 0.5 else "error",
                    "message": random.choice(ERROR_PATTERNS["db_connection"]),
                    "trace_id": f"trace_{random.randint(1000, 9999)}"
                })
            
            # Max connections
            metrics.append({
                "timestamp": timestamp.isoformat(),
                "service": service,
                "metric_name": "db_connections_active",
                "value": 100,
                "unit": "count"
            })
            
            # Very high latency
            metrics.append({
                "timestamp": timestamp.isoformat(),
                "service": service,
                "metric_name": "api_latency_ms",
                "value": random.uniform(4000, 6000),
                "unit": "milliseconds"
            })
        
        # Recovery (after mitigation)
        for i in range(25, duration_minutes):
            timestamp = start_time + timedelta(minutes=i)
            
            # Decreasing errors
            if random.random() < 0.1:
                logs.append({
                    "timestamp": timestamp.isoformat(),
                    "service": service,
                    "level": "warning",
                    "message": "Connection pool recovering",
                    "trace_id": f"trace_{random.randint(1000, 9999)}"
                })
            
            # Connections decreasing
            recovery_factor = (i - 25) / 5
            metrics.append({
                "timestamp": timestamp.isoformat(),
                "service": service,
                "metric_name": "db_connections_active",
                "value": max(50, 100 - recovery_factor * 10),
                "unit": "count"
            })
            
            # Latency normalizing
            metrics.append({
                "timestamp": timestamp.isoformat(),
                "service": service,
                "metric_name": "api_latency_ms",
                "value": max(200, 5000 - recovery_factor * 1000),
                "unit": "milliseconds"
            })
    
    elif incident_type == "memory_leak":
        # Simulate memory leak
        service = "user-service"
        
        for i in range(duration_minutes):
            timestamp = start_time + timedelta(minutes=i)
            
            # Memory growing linearly
            memory_usage = min(95, 40 + i * 1.5)
            
            metrics.append({
                "timestamp": timestamp.isoformat(),
                "service": service,
                "metric_name": "memory_usage_percent",
                "value": memory_usage,
                "unit": "percent"
            })
            
            # Errors start appearing when memory > 80%
            if memory_usage > 80 and random.random() < 0.4:
                logs.append({
                    "timestamp": timestamp.isoformat(),
                    "service": service,
                    "level": "error" if memory_usage < 90 else "critical",
                    "message": random.choice(ERROR_PATTERNS["memory"]),
                    "trace_id": f"trace_{random.randint(1000, 9999)}"
                })
    
    return logs, metrics


def main():
    print("🔧 Generating synthetic incident data...")
    
    # Generate DB connection exhaustion incident
    db_logs, db_metrics = generate_incident_scenario("db_connection", duration_minutes=30)
    
    # Generate memory leak incident
    mem_logs, mem_metrics = generate_incident_scenario("memory_leak", duration_minutes=40)
    
    # Combine all data
    all_logs = db_logs + mem_logs
    all_metrics = db_metrics + mem_metrics
    
    # Save to files
    with open("data/synthetic_logs.json", "w") as f:
        json.dump(all_logs, f, indent=2)
    
    with open("data/synthetic_metrics.json", "w") as f:
        json.dump(all_metrics, f, indent=2)
    
    print(f"✅ Generated {len(all_logs)} logs and {len(all_metrics)} metrics")
    print(f"📁 Saved to data/synthetic_logs.json and data/synthetic_metrics.json")
    print("\n📊 Incident scenarios created:")
    print("  1. Database connection pool exhaustion (payment-api)")
    print("  2. Memory leak (user-service)")
    print("\n💡 Use these files to test the incident analysis system")


if __name__ == "__main__":
    main()
