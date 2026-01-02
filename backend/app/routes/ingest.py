from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime

from app.models.log_models import LogEntry, MetricEntry
from app.db.sqlite_storage import storage

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
