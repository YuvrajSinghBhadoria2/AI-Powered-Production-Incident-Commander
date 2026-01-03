#!/usr/bin/env python3
import json
import time
import uuid
import random
from datetime import datetime, timedelta

def generate_otel_log_batch(service_name, message, level="ERROR", count=5):
    """Generates an OTLP resourceLogs batch"""
    timestamp_nano = int(time.time() * 1e9)
    
    log_records = []
    for _ in range(count):
        log_records.append({
            "timeUnixNano": str(timestamp_nano),
            "severityText": level,
            "severityNumber": 17 if level == "ERROR" else 9,
            "body": {"stringValue": message},
            "traceId": uuid.uuid4().hex,
            "spanId": uuid.uuid4().hex[:16],
            "attributes": [
                {"key": "http.method", "value": {"stringValue": "POST"}},
                {"key": "http.status_code", "value": {"stringValue": "500"}}
            ]
        })
        timestamp_nano += 1000000 # 1ms apart
        
    return {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": service_name}},
                        {"key": "deployment.environment", "value": {"stringValue": "production"}}
                    ]
                },
                "scopeLogs": [
                    {
                        "scope": {"name": "io.opentelemetry.demo"},
                        "logRecords": log_records
                    }
                ]
            }
        ]
    }

def generate_otel_metric_batch(service_name, metric_name, value, unit="ms"):
    """Generates an OTLP resourceMetrics batch"""
    timestamp_nano = int(time.time() * 1e9)
    
    return {
        "resourceMetrics": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": service_name}}
                    ]
                },
                "scopeMetrics": [
                    {
                        "scope": {"name": "io.opentelemetry.demo"},
                        "metrics": [
                            {
                                "name": metric_name,
                                "unit": unit,
                                "gauge": {
                                    "dataPoints": [
                                        {
                                            "timeUnixNano": str(timestamp_nano),
                                            "asDouble": float(value),
                                            "attributes": [
                                                {"key": "http.route", "value": {"stringValue": "/checkout"}}
                                            ]
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }

def main():
    print("🚀 Generating OTel Demo incident data...")
    
    # Scenario 1: Checkout Service failing because of Product Catalog
    checkout_logs = generate_otel_log_batch(
        "checkoutservice", 
        "Failed to fetch product details from productcatalogservice: timeout",
        count=10
    )
    
    catalog_logs = generate_otel_log_batch(
        "productcatalogservice",
        "Database connection pool exhausted",
        count=5
    )
    
    # Scenario 2: Recommendation Service Latency
    reco_metrics = generate_otel_metric_batch(
        "recommendationservice",
        "http.server.duration",
        value=2500.0
    )
    
    # Save samples
    with open("data/otel_checkout_failure.json", "w") as f:
        json.dump(checkout_logs, f, indent=2)
        
    with open("data/otel_catalog_failure.json", "w") as f:
        json.dump(catalog_logs, f, indent=2)
        
    with open("data/otel_reco_latency.json", "w") as f:
        json.dump(reco_metrics, f, indent=2)
        
    print("✅ Generated OTel sample files in data/ directory:")
    print("  - data/otel_checkout_failure.json")
    print("  - data/otel_catalog_failure.json")
    print("  - data/otel_reco_latency.json")

if __name__ == "__main__":
    main()
