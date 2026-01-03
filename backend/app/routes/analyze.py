import asyncio
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional

from app.models.log_models import AnalyzeIncidentRequest, AnalyzeIncidentResponse, Incident, RCAOutput
from app.db import storage
from app.services.incident_detection import incident_detector
from app.services.context_compression import context_compressor
from app.services.rag_engine import rag_engine
from app.services.llm_rca import llm_rca_engine
from app.services.security import get_api_key

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
async def analyze_incident(request: AnalyzeIncidentRequest, api_key: str = Depends(get_api_key)):
    """
    Analyze incidents within a time window or a specific incident.
    """
    start_analysis_time = time.time()
    
    try:
        # 1. Handle specific incident analysis if incident_id provided
        if request.incident_id:
            incident_data = await storage.get_incident(request.incident_id)
            if not incident_data:
                # If incident_id provided but not found, we still want to return a valid response
                # but maybe with an error or empty
                return AnalyzeIncidentResponse(
                    incidents_detected=[],
                    rca_results=[],
                    analysis_time_ms=round((time.time() - start_analysis_time) * 1000, 2)
                )
            
            # Use incident's service and timestamp to set window
            incident_time = datetime.fromisoformat(incident_data['timestamp'])
            start_time = incident_time - timedelta(minutes=30)
            end_time = incident_time + timedelta(minutes=5)
            
            logs = await storage.get_logs(start_time, end_time, incident_data['service'])
            metrics = await storage.get_metrics(start_time, end_time, incident_data['service'])
            
            detected_incidents = [incident_data]
        else:
            # 2. Standard detection-based analysis
            start_time, end_time = parse_time_window(request.time_window)
            
            logs = []
            metrics = []
            
            if request.services:
                for service in request.services:
                    logs.extend(await storage.get_logs(start_time, end_time, service))
                    metrics.extend(await storage.get_metrics(start_time, end_time, service))
            else:
                logs = await storage.get_logs(start_time, end_time)
                metrics = await storage.get_metrics(start_time, end_time)
            
            if not logs and not metrics:
                return AnalyzeIncidentResponse(
                    incidents_detected=[],
                    rca_results=[],
                    analysis_time_ms=round((time.time() - start_analysis_time) * 1000, 2)
                )
            
            detected_incidents = await incident_detector.detect_incidents(logs, metrics)
            
            if not detected_incidents:
                return AnalyzeIncidentResponse(
                    incidents_detected=[],
                    rca_results=[],
                    analysis_time_ms=round((time.time() - start_analysis_time) * 1000, 2)
                )
            
            # Store newly detected incidents
            for inc in detected_incidents:
                await storage.insert_incident(inc)
        
        # 3. Common RCA generation logic
        compressed_context = await context_compressor.compress(logs, metrics)
        rag_context = await rag_engine.get_relevant_context(compressed_context)
        
        async def run_single_rca(inc):
            try:
                # Ensure inc is a dict with 'id'
                return await llm_rca_engine.analyze_incident(
                    compressed_context=compressed_context,
                    rag_context=rag_context,
                    incident=inc
                )
            except Exception as e:
                print(f"Failed to generate RCA for incident {inc.get('id')}: {e}")
                return None

        rca_tasks = [run_single_rca(inc) for inc in detected_incidents]
        rca_results_list = await asyncio.gather(*rca_tasks)
        rca_results_list = [r for r in rca_results_list if r is not None]
        
        analysis_time_ms = round((time.time() - start_analysis_time) * 1000, 2)
        
        return AnalyzeIncidentResponse(
            incidents_detected=[Incident(**inc) for inc in detected_incidents],
            rca_results=[RCAOutput(**r) for r in rca_results_list],
            analysis_time_ms=analysis_time_ms
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/incidents")
async def get_incidents(limit: int = 50, api_key: str = Depends(get_api_key)):
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
async def get_incident(incident_id: str, api_key: str = Depends(get_api_key)):
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
