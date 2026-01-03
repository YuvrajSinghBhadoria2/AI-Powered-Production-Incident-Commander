from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime

from app.models.log_models import LogEntry, MetricEntry
from app.db.sqlite_storage import storage
from app.services.otel_mapper import otel_mapper

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/logs", status_code=status.HTTP_201_CREATED)
async def ingest_logs(logs: List[LogEntry]):
    """
    Ingest log entries.
    Accepts single log or batch of logs.
    """
    try:
        inserted_ids = []
        for log in logs:
            log_dict = log.model_dump()
            log_id = await storage.insert_log(log_dict)
            inserted_ids.append(log_id)
        
        return {
            "status": "success",
            "message": f"Ingested {len(logs)} log(s)",
            "inserted_ids": inserted_ids
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest logs: {str(e)}"
        )


@router.post("/logs/single", status_code=status.HTTP_201_CREATED)
async def ingest_single_log(log: LogEntry):
    """Ingest a single log entry"""
    try:
        log_dict = log.model_dump()
        log_id = await storage.insert_log(log_dict)
        
        return {
            "status": "success",
            "message": "Log ingested successfully",
            "log_id": log_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest log: {str(e)}"
        )


@router.post("/metrics", status_code=status.HTTP_201_CREATED)
async def ingest_metrics(metrics: List[MetricEntry]):
    """
    Ingest metric entries.
    Accepts single metric or batch of metrics.
    """
    try:
        inserted_ids = []
        for metric in metrics:
            metric_dict = metric.model_dump()
            metric_id = await storage.insert_metric(metric_dict)
            inserted_ids.append(metric_id)
        
        return {
            "status": "success",
            "message": f"Ingested {len(metrics)} metric(s)",
            "inserted_ids": inserted_ids
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest metrics: {str(e)}"
        )


@router.post("/metrics/single", status_code=status.HTTP_201_CREATED)
async def ingest_single_metric(metric: MetricEntry):
    """Ingest a single metric entry"""
    try:
        metric_dict = metric.model_dump()
        metric_id = await storage.insert_metric(metric_dict)
        
        return {
            "status": "success",
            "message": "Metric ingested successfully",
            "metric_id": metric_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest metric: {str(e)}"
        )
@router.post("/otel", status_code=status.HTTP_201_CREATED)
async def ingest_otel_data(payload: Dict[str, Any]):
    """
    Ingest raw OTLP JSON data (logs or metrics).
    """
    try:
        results = {
            "logs_ingested": 0,
            "metrics_ingested": 0,
            "log_ids": [],
            "metric_ids": []
        }
        
        # Check for logs
        if "resourceLogs" in payload:
            mapped_logs = otel_mapper.map_logs(payload)
            for log in mapped_logs:
                log_id = await storage.insert_log(log)
                results["log_ids"].append(log_id)
            results["logs_ingested"] = len(mapped_logs)
            
        # Check for metrics
        if "resourceMetrics" in payload:
            mapped_metrics = otel_mapper.map_metrics(payload)
            for metric in mapped_metrics:
                metric_id = await storage.insert_metric(metric)
                results["metric_ids"].append(metric_id)
            results["metrics_ingested"] = len(mapped_metrics)
            
        return {
            "status": "success",
            "message": f"Ingested {results['logs_ingested']} logs and {results['metrics_ingested']} metrics",
            "details": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest OTel data: {str(e)}"
        )


@router.post("/flush", status_code=status.HTTP_200_OK)
async def flush_all_data():
    """Flush all data from the database"""
    try:
        await storage.clear_all_data()
        return {
            "status": "success",
            "message": "All data flushed successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to flush data: {str(e)}"
        )
