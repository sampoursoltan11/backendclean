from strands import tool

@tool
async def add_risk_area(
    assessment_id: str,
    risk_area_id: str,
    context: dict = None
) -> dict:
    """
    Add a risk area to the assessment's active_risk_areas (user-driven, not document-dependent).
    Args:
        assessment_id: ID of the assessment
        risk_area_id: ID of the assessment
        risk_area_id: ID of the risk area to add
        context: Shared context dictionary
    Returns:
        Dictionary with update status
    """
    import logging
    logger = logging.getLogger(__name__)

    if context is None:
        context = {}
    try:
        logger.info(f"[ADD_RISK_AREA DEBUG] Called with assessment_id={assessment_id}, risk_area_id={risk_area_id}")
        db = get_db_service()
        assessment = await db.get_assessment(assessment_id)
        if not assessment:
            logger.error(f"[ADD_RISK_AREA DEBUG] Assessment not found!")
            context['last_error'] = f"Assessment {assessment_id} not found"
            return {"success": False, "error": f"Assessment {assessment_id} not found"}
        active_risk_areas = set(assessment.get('active_risk_areas', []))
        logger.info(f"[ADD_RISK_AREA DEBUG] Current active_risk_areas BEFORE add: {active_risk_areas}")
        if risk_area_id in active_risk_areas:
            logger.info(f"[ADD_RISK_AREA DEBUG] Risk area already exists, skipping")
            context['last_message'] = f"Risk area {risk_area_id} already attached to assessment."
            return {"success": True, "message": context['last_message']}
        active_risk_areas.add(risk_area_id)
        logger.info(f"[ADD_RISK_AREA DEBUG] active_risk_areas AFTER add: {list(active_risk_areas)}")
        await db.update_assessment(assessment_id, {"active_risk_areas": list(active_risk_areas)})
        logger.info(f"[ADD_RISK_AREA DEBUG] Successfully updated DynamoDB")
        context['last_message'] = f"Risk area {risk_area_id} added to assessment {assessment_id}."
        return {"success": True, "assessment_id": assessment_id, "risk_area_id": risk_area_id, "message": context['last_message']}
    except Exception as e:
        logger.error(f"[ADD_RISK_AREA DEBUG] ERROR: {e}", exc_info=True)
        context['last_error'] = str(e)
        return {"success": False, "error": str(e)}

@tool
async def remove_risk_area(
    assessment_id: str,
    risk_area_id: str,
    context: dict = None
) -> dict:
    """
    Remove a risk area from the assessment's active_risk_areas (user-driven, not document-dependent).
    Args:
        assessment_id: ID of the assessment
        risk_area_id: ID of the risk area to remove
        context: Shared context dictionary
    Returns:
        Dictionary with update status
    """
    if context is None:
        context = {}
    try:
        db = get_db_service()
        assessment = await db.get_assessment(assessment_id)
        if not assessment:
            context['last_error'] = f"Assessment {assessment_id} not found"
            return {"success": False, "error": f"Assessment {assessment_id} not found"}
        active_risk_areas = set(assessment.get('active_risk_areas', []))
        if risk_area_id not in active_risk_areas:
            context['last_message'] = f"Risk area {risk_area_id} is not attached to assessment."
            return {"success": True, "message": context['last_message']}
        active_risk_areas.remove(risk_area_id)
        await db.update_assessment(assessment_id, {"active_risk_areas": list(active_risk_areas)})
        context['last_message'] = f"Risk area {risk_area_id} removed from assessment {assessment_id}."
        return {"success": True, "assessment_id": assessment_id, "risk_area_id": risk_area_id, "message": context['last_message']}
    except Exception as e:
        context['last_error'] = str(e)
        return {"success": False, "error": str(e)}
"""
Assessment Management Tools - Strands 1.x Compatible
Tools for TRA assessment lifecycle management
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from strands import tool

from backend.services.dynamodb_service import DynamoDBService
from backend.models.tra_models import TraAssessment, AssessmentState


# Initialize service
_db_service: Optional[DynamoDBService] = None

def get_db_service() -> DynamoDBService:
    """Get singleton DynamoDB service."""
    global _db_service
    if _db_service is None:
        _db_service = DynamoDBService()
    return _db_service




@tool
async def create_assessment(
    project_name: str,
    system_id: str = "",
    classification: str = "",
    business_unit: str = "Default",
    description: str = "",
    session_id: str = "default",
    context: dict = None
) -> dict:
    """
    Create a new TRA assessment with complete project metadata.

    Args:
        project_name: Name of the project being assessed
        system_id: System/Project ID for tracking (e.g., SYS-2025-001)
        classification: Data classification (e.g., Confidential, Public, Internal)
        business_unit: Business unit owning the project
        description: Optional assessment description
        session_id: Session ID for tracking
        context: Shared context dictionary (for Strands best practice)
    Returns:
        Dictionary with assessment_id and creation details
    """
    import logging
    logging.debug(f"[TOOL DEBUG] create_assessment called (session_id={session_id})")
    if context is None:
        context = {}
    try:
        db = get_db_service()
        logging.debug(f"[TOOL DEBUG] create_assessment using AWS path: {getattr(db, '_use_aws', None)}")
        # Generate unique assessment ID
        assessment_id = f"TRA-2025-{uuid.uuid4().hex[:6].upper()}"
        # Create assessment object
        assessment = TraAssessment(
            assessment_id=assessment_id,
            session_id=session_id,
            title=project_name,
            description=description,
            system_id=system_id,
            classification=classification,
            business_unit=business_unit,
            requestor_name="System User",
            current_state=AssessmentState.DRAFT,
            completion_percentage=0.0,
            answers={},
            active_risk_areas=[],
            linked_documents=[],
            pk=f"ASSESSMENT#{assessment_id}",
            sk=f"METADATA#{datetime.utcnow().isoformat()}",
            gsi1_pk=f"SESSION#{session_id}",
            gsi1_sk=f"ASSESSMENT#{assessment_id}"
        )
        # Save to database
        await db.create_assessment(assessment)
        context['assessment_id'] = assessment_id
        context['assessment'] = assessment.dict()
        context['last_message'] = f"Assessment {assessment_id} created successfully"
        return {
            "success": True,
            "assessment_id": assessment_id,
            "project_name": project_name,
            "system_id": system_id,
            "classification": classification,
            "business_unit": business_unit,
            "status": "draft",
            "message": context['last_message']
        }
    except Exception as e:
        logging.error(f"[TOOL DEBUG] create_assessment error: {e}")
        context['last_error'] = str(e)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to create assessment: {str(e)}"
        }

@tool
async def update_assessment(
    assessment_id: str,
    updates: dict,
    context: dict = None
) -> dict:
    """
    Update an existing TRA assessment.
    Args:
        assessment_id: ID of the assessment to update
        updates: Dictionary of fields to update
        context: Shared context dictionary (for Strands best practice)
    Returns:
        Dictionary with update status
    """
    if context is None:
        context = {}
    try:
        db = get_db_service()
        updates["updated_at"] = datetime.utcnow()
        await db.update_assessment(assessment_id, updates)
        context['assessment_id'] = assessment_id
        context['updated_fields'] = list(updates.keys())
        context['last_message'] = f"Successfully updated assessment {assessment_id}"
        return {
            "success": True,
            "assessment_id": assessment_id,
            "updated_fields": context['updated_fields'],
            "message": context['last_message']
        }
    except Exception as e:
        context['last_error'] = str(e)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to update assessment: {str(e)}"
        }

@tool
async def list_assessments(
    session_id: str = None,
    status_filter: str = None,
    limit: int = 20,
    context: dict = None
) -> dict:
    """
    List TRA assessments with optional filtering.
    Args:
        session_id: Filter by session ID
        status_filter: Filter by status (draft, submitted, finalized)
        limit: Maximum number of results
        context: Shared context dictionary (for Strands best practice)
    Returns:
        Dictionary with list of assessments
    """
    import logging
    logging.debug(f"[TOOL DEBUG] list_assessments called (session_id={session_id}, status_filter={status_filter})")
    if context is None:
        context = {}
    try:
        db = get_db_service()
        logging.debug(f"[TOOL DEBUG] list_assessments using AWS path: {getattr(db, '_use_aws', None)}")
        # Use unified service for both filtered and global listing
        if status_filter:
            assessments = await db.query_assessments_by_state(status_filter)
        else:
            import aioboto3
            session = aioboto3.Session()
            async with session.client('dynamodb') as client:
                resp = await client.scan(
                    TableName=db.table_name,
                    FilterExpression='begins_with(pk, :pk_prefix)',
                    ExpressionAttributeValues={':pk_prefix': {'S': 'ASSESSMENT#'}},
                    Limit=limit,
                    ConsistentRead=True
                )
                items = resp.get('Items', [])
                logging.debug(f"[TOOL DEBUG] list_assessments DynamoDB scan items: {items}")
                assessments = [
                    {k: list(v.values())[0] for k, v in it.items()}
                    for it in items
                    if 'pk' in it and it['pk'].get('S', '').startswith('ASSESSMENT#')
                ]
        # Only filter by session_id if explicitly provided (for 'my assessments')
        if session_id is not None:
            logging.debug(f"[TOOL DEBUG] list_assessments filtering by session_id: {session_id}")
            assessments = [a for a in assessments if a.get('session_id') == session_id]
        context['assessments'] = assessments
        context['last_message'] = f"Found {len(assessments)} assessments."
        return {
            "success": True,
            "assessments": assessments,
            "count": len(assessments),
            "filters": {
                "session_id": session_id,
                "status": status_filter
            }
        }
    except Exception as e:
        if context is None:
            context = {}
        context['last_error'] = str(e)
        logging.error(f"[TOOL DEBUG] list_assessments error: {e}")
        return {
            "success": False,
            "error": str(e),
            "count": 0,
            "assessments": []
        }

@tool
async def get_assessment(
    assessment_id: str,
    context: dict = None
) -> dict:
    """
    Retrieve a single assessment by ID (context-aware).
    Args:
        assessment_id: ID of the assessment to retrieve
        context: Shared context dictionary (for Strands best practice)
    Returns:
        Dictionary with assessment details
    """
    if context is None:
        context = {}
    try:
        db = get_db_service()
        assessment = await db.get_assessment(assessment_id)
        if not assessment:
            context['last_error'] = f"Assessment {assessment_id} not found"
            return {
                "success": False,
                "error": f"Assessment {assessment_id} not found"
            }
        context['assessment'] = assessment
        context['last_message'] = f"Assessment {assessment_id} retrieved successfully"
        return {
            "success": True,
            "assessment_id": assessment_id,
            "assessment": assessment,
            "message": context['last_message']
        }
    except Exception as e:
        context['last_error'] = str(e)
        return {
            "success": False,
            "error": str(e)
        }

@tool
async def switch_assessment(
    new_assessment_id: str,
    session_id: str,
    context: dict = None
) -> dict:
    """
    Switch the active assessment for a session.
    
    Args:
        context['assessments'] = assessments
        context['last_message'] = f"Found {len(assessments)} assessments."
        new_assessment_id: ID of the assessment to switch to
        session_id: Current session ID
    
    Returns:
        Dictionary with switch confirmation
    """
    if context is None:
        context = {}
    try:
        db = get_db_service()
        # Verify assessment exists
        assessment = await db.get_assessment(new_assessment_id)
        if not assessment:
            context['last_error'] = f"Assessment {new_assessment_id} not found"
            return {
                "success": False,
                "error": f"Assessment {new_assessment_id} not found"
            }
        # In a real implementation, update session state
        # For now, just confirm the switch
        context['switched_to'] = new_assessment_id
        context['assessment_title'] = assessment.get('title', 'Untitled')
        context['last_message'] = f"Switched to assessment {new_assessment_id}"
        return {
            "success": True,
            "switched_to": new_assessment_id,
            "assessment_title": assessment.get('title', 'Untitled'),
            "session_id": session_id,
            "message": context['last_message']
        }
    except Exception as e:
        context['last_error'] = str(e)
        return {
            "success": False,
            "error": str(e)
        }
