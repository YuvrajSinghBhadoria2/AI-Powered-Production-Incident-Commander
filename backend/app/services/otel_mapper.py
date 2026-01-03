from datetime import datetime
from typing import List, Dict, Any, Optional
import json

class OTelMapper:
    """
    Maps OTLP JSON (logs and metrics) to internally understood LogEntry and MetricEntry.
    """
    
    @staticmethod
    def map_logs(otel_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses OTLP logs JSON and returns a list of internal LogEntry dicts.
        Structure: resource_logs -> scope_logs -> log_records
        """
        mapped_logs = []
        resource_logs = otel_json.get("resourceLogs", [])
        
        for resource_log in resource_logs:
            resource_attrs = {
                attr["key"]: attr["value"].get("stringValue") 
                for attr in resource_log.get("resource", {}).get("attributes", [])
            }
            service_name = resource_attrs.get("service.name", "unknown")
            
            scope_logs = resource_log.get("scopeLogs", [])
            for scope_log in scope_logs:
                log_records = scope_log.get("logRecords", [])
                for record in log_records:
                    # OTLP timestamps are in nanoseconds
                    ts_nano = int(record.get("timeUnixNano", 0))
                    timestamp = datetime.fromtimestamp(ts_nano / 1e9)
                    
                    body = record.get("body", {})
                    message = body.get("stringValue") or body.get("intVlaue") or str(body)
                    
                    severity_text = record.get("severityText", "INFO").lower()
                    
                    # Map OTel severity to our LogLevel
                    level = "info"
                    if "error" in severity_text or "fatal" in severity_text:
                        level = "error"
                    elif "warn" in severity_text:
                        level = "warning"
                    elif "debug" in severity_text:
                        level = "debug"
                    
                    mapped_logs.append({
                        "timestamp": timestamp,
                        "service": service_name,
                        "level": level,
                        "message": message,
                        "trace_id": record.get("traceId"),
                        "metadata": {
                            "severity_number": record.get("severityNumber"),
                            "attributes": {
                                attr["key"]: attr["value"].get("stringValue") 
                                for attr in record.get("attributes", [])
                            }
                        }
                    })
        
        return mapped_logs

    @staticmethod
    def map_metrics(otel_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses OTLP metrics JSON and returns a list of internal MetricEntry dicts.
        Structure: resource_metrics -> scope_metrics -> metrics -> (gauge/sum/histogram) -> data_points
        """
        mapped_metrics = []
        resource_metrics = otel_json.get("resourceMetrics", [])
        
        for resource_metric in resource_metrics:
            resource_attrs = {
                attr["key"]: attr["value"].get("stringValue") 
                for attr in resource_metric.get("resource", {}).get("attributes", [])
            }
            service_name = resource_attrs.get("service.name", "unknown")
            
            scope_metrics = resource_metric.get("scopeMetrics", [])
            for scope_metric in scope_metrics:
                metrics = scope_metric.get("metrics", [])
                for metric in metrics:
                    metric_name = metric.get("name")
                    unit = metric.get("unit", "1")
                    
                    # Handle different metric types (Gauge, Sum, Histogram, etc.)
                    # For simplicity, we'll look for dataPoints in common types
                    data_points = []
                    if "gauge" in metric:
                        data_points = metric["gauge"].get("dataPoints", [])
                    elif "sum" in metric:
                        data_points = metric["sum"].get("dataPoints", [])
                    elif "histogram" in metric:
                        # For histograms, we might take the sum or average
                        data_points = metric["histogram"].get("dataPoints", [])
                    
                    for dp in data_points:
                        ts_nano = int(dp.get("timeUnixNano", 0))
                        timestamp = datetime.fromtimestamp(ts_nano / 1e9)
                        
                        # Extract value (as_double or as_int)
                        value = dp.get("asDouble") or dp.get("asInt")
                        
                        # If it's a histogram point, use the sum or explicit value
                        if value is None and "sum" in dp:
                            value = dp["sum"]
                        
                        if value is not None:
                            tags = {
                                attr["key"]: attr["value"].get("stringValue")
                                for attr in dp.get("attributes", [])
                            }
                            
                            mapped_metrics.append({
                                "timestamp": timestamp,
                                "service": service_name,
                                "metric_name": metric_name,
                                "value": float(value),
                                "unit": unit,
                                "tags": tags
                            })
                            
        return mapped_metrics

otel_mapper = OTelMapper()
