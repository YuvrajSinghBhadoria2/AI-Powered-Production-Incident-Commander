from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
from typing import Optional
import time

from app.models.log_models import AnalyzeIncidentRequest, AnalyzeIncidentResponse, Incident
from app.db.sqlite_storage import storage
from app.services.incident_detection import incident_detector
from app.services.context_compression import context_compressor
from app.services.rag_engine import rag_engine
from app.services.llm_rca import llm_rca_engine

router = APIRouter(prefix="/analyze", tags=["analysis"])


def parse_time_window(time_window: str) -> tuple[datetime, datetime]:
    """Parse time window string to datetime range"""
    now = datetime.now()
    
    time_map = {
        "last_15_min": timedelta(minutes=15),
        "last_30_min": timedelta(minutes=30),
        "last_1_hour": timedelta(hours=1),
        "last_6_hours": timedelta(hours=6),
        "last_24_hours": timedelta(hours=24),
    }
    
    delta = time_map.get(time_window, timedelta(minutes=30))
    start_time = now - delta
    
    return start_time, now


@router.post("/incident", response_model=AnalyzeIncidentResponse)
async def analyze_incident(request: AnalyzeIncidentRequest):
    """
    Analyze incidents within a time window.
    
    Steps:
    1. Retrieve logs and metrics
    2. Detect incidents
    3. Compress context
    4. Get RAG context
    5. Run LLM RCA
    6. Return results
    """
    start_analysis_time = time.time()
    
    try:
        # Parse time window
        start_time, end_time = parse_time_window(request.time_window)
        
        # Retrieve logs and metrics
        logs = []
        metrics = []
        
        if request.services:
            for service in request.services:
                service_logs = await storage.get_logs(start_time, end_time, service)
                service_metrics = await storage.get_metrics(start_time, end_time, service)
                logs.extend(service_logs)
                metrics.extend(service_metrics)
        else:
            logs = await storage.get_logs(start_time, end_time)
            metrics = await storage.get_metrics(start_time, end_time)
        
        if not logs and not metrics:
            return AnalyzeIncidentResponse(
                incidents_detected=[],
                rca_results=None,
                analysis_time_ms=round((time.time() - start_analysis_time) * 1000, 2)
            )
        
        # Detect incidents
        detected_incidents = await incident_detector.detect_incidents(logs, metrics)
        
        if not detected_incidents:
            return AnalyzeIncidentResponse(
                incidents_detected=[],
                rca_results=None,
                analysis_time_ms=round((time.time() - start_analysis_time) * 1000, 2)
            )
        
        # Store incidents
        for inc in detected_incidents:
            await storage.insert_incident(inc)
        
        # Analyze the most severe incident
        primary_incident = max(
            detected_incidents,
            key=lambda x: {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}.get(x['severity'], 0)
        )
        
        # Compress context
        compressed_context = await context_compressor.compress(logs, metrics)
        
        # Get RAG context
        rag_context = await rag_engine.get_relevant_context(compressed_context)
        
        # Run LLM RCA
        rca_results = await llm_rca_engine.analyze_incident(
            compressed_context=compressed_context,
            rag_context=rag_context,
            incident=primary_incident
        )
        
        analysis_time_ms = round((time.time() - start_analysis_time) * 1000, 2)
        
        return AnalyzeIncidentResponse(
            incidents_detected=[Incident(**inc) for inc in detected_incidents],
            rca_results=rca_results,
            analysis_time_ms=analysis_time_ms
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/incidents")
async def get_incidents(limit: int = 50):
    """Get recent incidents"""
    try:
        incidents = await storage.get_all_incidents(limit)
        return {
            "status": "success",
            "count": len(incidents),
            "incidents": incidents
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve incidents: {str(e)}"
        )


@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get specific incident by ID"""
    try:
        incident = await storage.get_incident(incident_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident {incident_id} not found"
            )
        return incident
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve incident: {str(e)}"
        )
