from fastapi import APIRouter, HTTPException, status
from typing import List

from app.models.log_models import Postmortem
from app.db.sqlite_storage import storage
from app.services.llm_rca import llm_rca_engine

router = APIRouter(prefix="/postmortem", tags=["postmortem"])


@router.get("/{incident_id}", response_model=Postmortem)
async def get_postmortem(incident_id: str):
    """
    Get or generate postmortem for an incident.
    If postmortem doesn't exist, generates it from RCA.
    """
    try:
        # Check if postmortem already exists
        existing_postmortem = await storage.get_postmortem(incident_id)
        if existing_postmortem:
            return Postmortem(**existing_postmortem)
        
        # Get incident details
        incident = await storage.get_incident(incident_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident {incident_id} not found"
            )
        
        # For now, return a message that postmortem needs to be generated
        # In a full implementation, this would trigger RCA if not already done
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Postmortem for incident {incident_id} not found. Run analysis first."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve postmortem: {str(e)}"
        )


@router.post("/{incident_id}", response_model=Postmortem, status_code=status.HTTP_201_CREATED)
async def create_postmortem(incident_id: str):
    """
    Generate postmortem for an incident.
    Requires that RCA has been performed.
    """
    try:
        # Get incident
        incident = await storage.get_incident(incident_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident {incident_id} not found"
            )
        
        # Check if postmortem already exists
        existing_postmortem = await storage.get_postmortem(incident_id)
        if existing_postmortem:
            return Postmortem(**existing_postmortem)
        
        # For a complete implementation, we'd need to store RCA results
        # For now, generate a basic postmortem
        # In production, this would use stored RCA output
        
        # Create a mock RCA output for postmortem generation
        mock_rca = {
            'root_cause': incident.get('description', 'Unknown'),
            'timeline': [
                {
                    'timestamp': incident.get('timestamp', ''),
                    'event': 'Incident detected',
                    'impact': incident.get('description', '')
                }
            ],
            'mitigation_steps': [
                'Investigate root cause',
                'Implement monitoring',
                'Create runbook'
            ],
            'similar_incidents': []
        }
        
        # Generate postmortem
        postmortem_data = await llm_rca_engine.generate_postmortem(mock_rca, incident)
        
        # Store postmortem
        await storage.insert_postmortem(postmortem_data)
        
        return Postmortem(**postmortem_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create postmortem: {str(e)}"
        )


@router.get("/", response_model=List[Postmortem])
async def list_postmortems(limit: int = 20):
    """List recent postmortems"""
    try:
        # Get recent incidents
        incidents = await storage.get_all_incidents(limit)
        
        postmortems = []
        for incident in incidents:
            postmortem = await storage.get_postmortem(incident['id'])
            if postmortem:
                postmortems.append(Postmortem(**postmortem))
        
        return postmortems
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list postmortems: {str(e)}"
        )
