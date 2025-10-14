"""
Risk Area Management Tools - Strands 1.x Compatible
Tools for managing active risk areas in TRA assessments
"""

from typing import List, Dict, Any
from strands import tool

from backend.services.dynamodb_service import DynamoDBService
from backend.tools.question_tools import get_decision_tree


# Initialize service
_db_service = None

def get_db_service() -> DynamoDBService:
    """Get singleton DynamoDB service."""
    global _db_service
    if _db_service is None:
        _db_service = DynamoDBService()
    return _db_service


@tool
async def add_risk_area(
    assessment_id: str,
    risk_area_id: str
) -> dict:
    """
    Add a risk area to an assessment's active risk areas.
    
    Args:
        assessment_id: ID of the assessment
        risk_area_id: Risk area to add (e.g., 'data_security', 'infrastructure_security')
    
    Returns:
        Dictionary with success status
    """
    try:
        db = get_db_service()
        
        # Get current assessment
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            return {
                "success": False,
                "error": f"Assessment {assessment_id} not found"
            }
        
        # Get current risk areas
        active_risk_areas = assessment.get('active_risk_areas', [])
        
        # Add if not already present
        if risk_area_id not in active_risk_areas:
            active_risk_areas.append(risk_area_id)
            
            # Update assessment
            await db.update_assessment(assessment_id, {
                "active_risk_areas": active_risk_areas
            })
            
            return {
                "success": True,
                "assessment_id": assessment_id,
                "risk_area_added": risk_area_id,
                "active_risk_areas": active_risk_areas,
                "message": f"Added {risk_area_id} to assessment"
            }
        else:
            return {
                "success": True,
                "assessment_id": assessment_id,
                "message": f"{risk_area_id} already in active risk areas",
                "active_risk_areas": active_risk_areas
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
def list_standard_risk_areas() -> dict:
    """
    List all available standard risk areas from the decision tree configuration.
    Use this when the user asks to see available risk areas or wants to select from standard risk areas.

    Returns:
        Dictionary with list of available risk areas
    """
    try:
        decision_tree = get_decision_tree()
        risk_areas = decision_tree.get("risk_areas", {})

        if not risk_areas:
            return {
                "success": False,
                "error": "No risk areas configured in decision tree"
            }

        # Format risk areas for display
        # Handle both dict format (decision_tree2.yaml) and list format (decision_tree.yaml)
        formatted_areas = []

        if isinstance(risk_areas, dict):
            # decision_tree2.yaml format: dict with keys like 'third_party', 'data_privacy'
            for area_id, area_data in risk_areas.items():
                formatted_areas.append({
                    "id": area_id,
                    "name": area_data.get("name", area_id.replace('_', ' ').title()),
                    "description": area_data.get("description", f"Questions related to {area_data.get('name', area_id)}"),
                    "icon": area_data.get("icon", "📋")
                })
        elif isinstance(risk_areas, list):
            # decision_tree.yaml format: list of dicts with 'id', 'name', etc.
            for area in risk_areas:
                formatted_areas.append({
                    "id": area.get("id"),
                    "name": area.get("name"),
                    "description": area.get("description", ""),
                    "icon": area.get("icon", "")
                })

        return {
            "success": True,
            "risk_areas": formatted_areas,
            "count": len(formatted_areas),
            "message": f"Found {len(formatted_areas)} standard risk areas"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def remove_risk_area(
    assessment_id: str,
    risk_area_id: str
) -> dict:
    """
    Remove a risk area from an assessment's active risk areas.
    
    Args:
        assessment_id: ID of the assessment
        risk_area_id: Risk area to remove
    
    Returns:
        Dictionary with success status
    """
    try:
        db = get_db_service()
        
        # Get current assessment
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            return {
                "success": False,
                "error": f"Assessment {assessment_id} not found"
            }
        
        # Get current risk areas
        active_risk_areas = assessment.get('active_risk_areas', [])
        
        # Remove if present
        if risk_area_id in active_risk_areas:
            active_risk_areas.remove(risk_area_id)
            
            # Update assessment
            await db.update_assessment(assessment_id, {
                "active_risk_areas": active_risk_areas
            })
            
            return {
                "success": True,
                "assessment_id": assessment_id,
                "risk_area_removed": risk_area_id,
                "active_risk_areas": active_risk_areas,
                "message": f"Removed {risk_area_id} from assessment"
            }
        else:
            return {
                "success": True,
                "assessment_id": assessment_id,
                "message": f"{risk_area_id} not in active risk areas",
                "active_risk_areas": active_risk_areas
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def set_risk_areas(
    assessment_id: str,
    risk_area_ids: List[str]
) -> dict:
    """
    Set the complete list of active risk areas for an assessment.
    
    Args:
        assessment_id: ID of the assessment
        risk_area_ids: List of risk area IDs to set
    
    Returns:
        Dictionary with success status
    """
    try:
        db = get_db_service()
        
        # Update assessment with new risk areas
        await db.update_assessment(assessment_id, {
            "active_risk_areas": risk_area_ids
        })
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "active_risk_areas": risk_area_ids,
            "count": len(risk_area_ids),
            "message": f"Set {len(risk_area_ids)} active risk areas"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def link_document(
    assessment_id: str,
    filename: str,
    s3_key: str = "",
    risk_areas_identified: List[str] = None
) -> dict:
    """
    Link a document to an assessment.
    
    Args:
        assessment_id: ID of the assessment
        filename: Name of the document file
        s3_key: S3 key where document is stored
        risk_areas_identified: Risk areas identified from this document
    
    Returns:
        Dictionary with success status
    """
    try:
        from datetime import datetime
        
        db = get_db_service()
        
        # Get current assessment
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            return {
                "success": False,
                "error": f"Assessment {assessment_id} not found"
            }
        
        # Get current linked documents
        linked_documents = assessment.get('linked_documents', [])
        
        # Check if document already linked
        existing = next((doc for doc in linked_documents if doc.get('filename') == filename), None)
        
        if existing:
            # Update existing entry
            existing['risk_areas_identified'] = risk_areas_identified or []
            existing['updated_at'] = datetime.utcnow().isoformat()
        else:
            # Add new document link
            linked_documents.append({
                "filename": filename,
                "s3_key": s3_key or f"session/{assessment.get('session_id')}/{filename}",
                "upload_date": datetime.utcnow().isoformat(),
                "risk_areas_identified": risk_areas_identified or []
            })
        
        # Update assessment
        await db.update_assessment(assessment_id, {
            "linked_documents": linked_documents
        })
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "document_linked": filename,
            "risk_areas_identified": risk_areas_identified or [],
            "total_documents": len(linked_documents),
            "message": f"Linked document {filename} to assessment"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
