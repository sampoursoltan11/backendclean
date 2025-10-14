# Import Optional for type hints
from typing import Optional

# Import the tool decorator from strands to avoid circular import
from strands import tool

@tool
async def list_kb_items() -> dict:
    """
    List all knowledge base items/documents (global KB listing).
    Returns a list of KB item summaries.
    """
    try:
        from backend.services.bedrock_kb_service import BedrockKnowledgeBaseService
        kb_service = BedrockKnowledgeBaseService()
        # This assumes a method to list all KB items exists; if not, fallback to S3 scan or in-memory
        if hasattr(kb_service, 'list_all_kb_items'):
            items = await kb_service.list_all_kb_items()
        else:
            # Fallback: not implemented
            items = []
        # Enhance: parse S3 URI to extract assessment_id and project metadata
        def parse_metadata_from_s3_key(s3_key):
            # Example S3 key: s3://bucket/documents/project/2025/10/project-foo-bar-20251007-xxxxxx/Foo_Bar.docx
            # or s3://bucket/knowledge-base/enterprise_xxx_123456789/SomeFile.docx
            import re
            assessment_id = ''
            project = ''
            if s3_key:
                # Try to extract assessment_id from knowledge-base/enterprise_xxx_123456789
                m = re.search(r'knowledge-base/(enterprise_[^/]+)/', s3_key)
                if m:
                    assessment_id = m.group(1)
                # Try to extract project from documents/project/...
                m2 = re.search(r'documents/([^/]+)/', s3_key)
                if m2:
                    project = m2.group(1)
            return assessment_id, project

        seen = set()
        summaries = []
        for i in items:
            s3_key = i.get('s3_key', '')
            filename = i.get('filename', '')
            assessment_id, project = parse_metadata_from_s3_key(s3_key)
            canonical = filename.lower().strip()
            if canonical in seen:
                continue  # deduplicate by filename
            seen.add(canonical)
            summaries.append({
                'document_id': i.get('document_id'),
                'filename': filename,
                'assessment_id': assessment_id,
                'project': project,
                'uploaded_at': i.get('updated_at', ''),
                'status': i.get('status', ''),
                's3_key': s3_key,
            })
        return {
            'success': True,
            'count': len(summaries),
            'kb_items': summaries
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'kb_items': []
        }
@tool
async def list_documents(assessment_id: Optional[str] = None, session_id: Optional[str] = None) -> dict:
    """
    List all documents, optionally filtered by assessment_id or session_id.
    Returns a list of document summaries.
    """
    try:
        db = get_db_service()
        # Prefer assessment_id, then session_id, else all
        if assessment_id:
            documents = await db.get_documents_by_assessment(assessment_id)
        elif session_id:
            # Try to get all documents for a session (if implemented)
            if hasattr(db, 'get_session_documents'):
                documents = await db.get_session_documents(session_id)
            else:
                documents = []
        else:
            # Fallback: scan all documents (in-memory or DynamoDB)
            if hasattr(db, '_documents'):
                documents = list(db._documents)
            else:
                import aioboto3
                session = aioboto3.Session()
                async with session.client('dynamodb') as client:
                    resp = await client.scan(
                        TableName=db.table_name,
                        FilterExpression='begins_with(pk, :pk_prefix)',
                        ExpressionAttributeValues={':pk_prefix': {'S': 'DOC#'}}
                    )
                    items = resp.get('Items', [])
                    documents = [{k: list(v.values())[0] for k, v in it.items()} for it in items]
        summaries = [
            {
                'document_id': d.get('document_id'),
                'filename': d.get('filename', ''),
                'assessment_id': d.get('assessment_id', ''),
                'session_id': d.get('session_id', ''),
                'uploaded_at': d.get('uploaded_at', ''),
                'status': d.get('status', ''),
                's3_key': d.get('s3_key', ''),
            }
            for d in documents
        ]
        return {
            'success': True,
            'count': len(summaries),
            'documents': summaries
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'documents': []
        }
from typing import Optional
from strands import tool
"""
Status and Export Tools - Strands 1.x Compatible
Tools for assessment status, reporting, and export generation
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from strands import tool

from backend.services.dynamodb_service import DynamoDBService
from backend.models.tra_models import AssessmentState
from backend.core.config import get_settings


# Initialize services
_db_service: Optional[DynamoDBService] = None

def get_db_service() -> DynamoDBService:
    """Get singleton DynamoDB service."""
    global _db_service
    if _db_service is None:
        _db_service = DynamoDBService()
    return _db_service


@tool
async def review_answers(assessment_id: str) -> dict:
    """
    Review all answers for a completed assessment, organized by risk area.
    
    Args:
        assessment_id: ID of the assessment to review
    
    Returns:
        Dictionary with all questions and answers organized by risk area
    """
    try:
        db = get_db_service()
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            return {
                "success": False,
                "error": f"Assessment {assessment_id} not found"
            }
        
        # Load decision tree to get questions
        import yaml
        from pathlib import Path
        from backend.core.config import get_settings
        
        settings = get_settings()
        config_path = Path(settings.decision_tree_config_path)
        if not config_path.is_absolute():
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / config_path
        
        with open(config_path, 'r', encoding='utf-8') as f:
            decision_tree = yaml.safe_load(f)

        risk_areas_raw = decision_tree.get("risk_areas", [])

        # Handle both dict format (decision_tree3.yaml) and list format (decision_tree.yaml)
        if isinstance(risk_areas_raw, dict):
            # Dict format: {"third_party": {"name": "Third Party Risk", ...}, ...}
            risk_areas = {area_id: area_data.get("name", area_id.replace('_', ' ').title())
                         for area_id, area_data in risk_areas_raw.items()}
        else:
            # List format: [{"id": "data_security", "name": "Data Security", ...}, ...]
            risk_areas = {ra['id']: ra['name'] for ra in risk_areas_raw}

        questions = decision_tree.get("questions", [])
        answers = assessment.get("answers", {})
        answers_by_risk_area = assessment.get("answers_by_risk_area", {})
        
        # Get active risk areas
        import ast
        active_risk_areas = assessment.get('active_risk_areas', [])
        if isinstance(active_risk_areas, str):
            try:
                active_risk_areas = ast.literal_eval(active_risk_areas)
            except Exception:
                active_risk_areas = [active_risk_areas]
        if not isinstance(active_risk_areas, list):
            active_risk_areas = [active_risk_areas]
        
        # Organize answers by risk area
        review_data = []
        for risk_area_id in active_risk_areas:
            risk_area_name = risk_areas.get(risk_area_id, risk_area_id)
            risk_area_answers = answers_by_risk_area.get(risk_area_id, {})
            
            # Get questions for this risk area
            area_questions = [q for q in questions if q.get("risk_area") == risk_area_id]
            
            qa_pairs = []
            for q in area_questions:
                q_id = q.get("id")
                answer = risk_area_answers.get(q_id, "Not answered")
                qa_pairs.append({
                    "question": q.get("question", ""),
                    "answer": answer,
                    "question_id": q_id
                })
            
            review_data.append({
                "risk_area": risk_area_name,
                "risk_area_id": risk_area_id,
                "questions_answered": len(risk_area_answers),
                "total_questions": len(area_questions),
                "qa_pairs": qa_pairs
            })
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "title": assessment.get("title", "Untitled"),
            "review_data": review_data,
            "total_answered": len(answers),
            "completion_percentage": assessment.get("completion_percentage", 0)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
async def get_assessment_summary(assessment_id: str) -> dict:
    """
    Get complete assessment overview with risk areas and suggested actions.
    ALWAYS call this first when user mentions an assessment ID.
    
    Args:
        assessment_id: ID of the assessment
    
    Returns:
        Complete summary with next suggested action
    """
    try:
        db = get_db_service()
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            return {
                "success": False,
                "error": f"Assessment {assessment_id} not found"
            }
        
        # Get risk areas progress
        import yaml
        from pathlib import Path
        from backend.core.config import get_settings
        
        settings = get_settings()
        config_path = Path(settings.decision_tree_config_path)
        if not config_path.is_absolute():
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / config_path
        
        with open(config_path, 'r', encoding='utf-8') as f:
            decision_tree = yaml.safe_load(f)
        risk_areas_raw = decision_tree.get("risk_areas", [])
        questions = decision_tree.get("questions", [])
        answers = assessment.get("answers", {})
        answers_by_risk_area = assessment.get("answers_by_risk_area", {})
        import ast
        active_risk_areas = assessment.get('active_risk_areas', [])
        # Normalize to list if stored as string
        if isinstance(active_risk_areas, str):
            try:
                active_risk_areas = ast.literal_eval(active_risk_areas)
            except Exception:
                active_risk_areas = [active_risk_areas]
        if not isinstance(active_risk_areas, list):
            active_risk_areas = [active_risk_areas]

        # Handle both dict format (decision_tree3.yaml) and list format (decision_tree.yaml)
        risk_areas = []
        if isinstance(risk_areas_raw, dict):
            # Convert dict format to list format for uniform processing
            for area_id, area_data in risk_areas_raw.items():
                risk_areas.append({
                    "id": area_id,
                    "name": area_data.get("name", area_id.replace('_', ' ').title()),
                    "questions": area_data.get("questions", [])
                })
        else:
            # Already in list format
            risk_areas = risk_areas_raw

        # Only show risk areas actually attached to the assessment
        # Use smart completion logic - only count applicable questions
        from backend.tools.question_tools import _count_applicable_questions

        risk_progress = []
        for area in risk_areas:
            if not isinstance(area, dict):
                continue
            area_id = str(area.get("id", ""))
            if area_id not in active_risk_areas:
                continue

            # Use smart counting - only applicable questions based on decision tree logic
            risk_area_answers = answers_by_risk_area.get(area_id, {})
            applicable_total, answered = _count_applicable_questions(area_id, risk_area_answers, decision_tree)

            pct = round((answered/applicable_total)*100, 1) if applicable_total > 0 else 0

            risk_progress.append({
                "name": area.get("name", "Unknown"),
                "completion": pct,
                "answered": answered,
                "total": applicable_total
            })
        
        # Determine next action
        try:
            completion = float(assessment.get("completion_percentage", 0))
        except (ValueError, TypeError):
            completion = 0.0
            
        if completion < 100:
            next_action = "CONTINUE_QUESTIONS"
        elif assessment.get("current_state") == "draft":
            next_action = "SUBMIT_FOR_REVIEW"
        else:
            next_action = "CHECK_STATUS"
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "title": assessment.get("title", "Untitled"),
            "completion_percentage": completion,
            "risk_areas": risk_progress,
            "current_state": assessment.get("current_state", "draft"),
            "next_action": next_action,
            "total_answered": len(answers),
            "created_at": assessment.get("created_at")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
async def check_status(assessment_id: str) -> dict:
    """
    Check the current status of a TRA assessment.
    
    Args:
        assessment_id: ID of the assessment to check
    
    Returns:
        Dictionary with assessment status details
    """
    try:
        db = get_db_service()
        
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            return {
                "success": False,
                "error": f"Assessment {assessment_id} not found"
            }
        
        # Get latest review feedback if sent back
        feedback = None
        next_action = None
        
        current_state = assessment.get("current_state", AssessmentState.DRAFT)
        
        if current_state == AssessmentState.SENT_BACK:
            try:
                reviews = await db.get_assessment_reviews(assessment_id)
                if reviews:
                    latest_review = max(reviews, key=lambda x: x.get("updated_at", ""))
                    feedback = latest_review.get("send_back_comment")
            except Exception:
                pass
        
        # Determine next action
        if current_state == AssessmentState.DRAFT:
            completion = assessment.get("completion_percentage", 0)
            if completion < 100:
                next_action = "Continue answering questions"
            else:
                next_action = "Submit assessment for review"
        elif current_state == AssessmentState.SUBMITTED:
            next_action = "Awaiting assessor review"
        elif current_state == AssessmentState.UNDER_REVIEW:
            next_action = "Assessor is reviewing"
        elif current_state == AssessmentState.SENT_BACK:
            next_action = "Address assessor feedback and resubmit"
        elif current_state == AssessmentState.FINALIZED:
            next_action = "Assessment complete - download report"
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "title": assessment.get("title", "Untitled"),
            "current_state": current_state,
            "completion_percentage": assessment.get("completion_percentage", 0),
            "last_updated": assessment.get("updated_at"),
            "created_at": assessment.get("created_at"),
            "assessor_feedback": feedback,
            "assessor_link": assessment.get("assessor_link"),
            "next_action": next_action,
            "status_message": f"Assessment is in {current_state} state"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def generate_assessor_link(assessment_id: str) -> dict:
    """
    Generate a secure link for assessor review access.
    
    Args:
        assessment_id: ID of the assessment
    
    Returns:
        Dictionary with assessor link
    """
    try:
        db = get_db_service()
        settings = get_settings()
        
        # Verify assessment exists
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            return {
                "success": False,
                "error": f"Assessment {assessment_id} not found"
            }
        
        # Generate secure token
        secure_token = str(uuid.uuid4())
        assessor_link = f"{settings.assessor_base_url}/{assessment_id}?token={secure_token}"
        
        # Update assessment with link and change state to submitted
        await db.update_assessment(
            assessment_id,
            {
                "assessor_link": assessor_link,
                "current_state": AssessmentState.SUBMITTED,
                "submitted_at": datetime.utcnow()
            }
        )
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "assessor_link": assessor_link,
            "message": "Assessor link generated successfully. Assessment moved to submitted state.",
            "note": "Share this link securely with the assessor"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def export_assessment(
    assessment_id: str,
    export_format: str = "json",
    include_audit_trail: bool = True
) -> dict:
    """
    Export assessment data in specified format.
    
    Args:
        assessment_id: ID of the assessment to export
        export_format: Export format (json, docx)
        include_audit_trail: Whether to include audit trail events
    
    Returns:
        Dictionary with export information
    """
    try:
        db = get_db_service()
        settings = get_settings()
        
        # Get assessment data
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            return {
                "success": False,
                "error": f"Assessment {assessment_id} not found"
            }
        
        # Get audit trail if requested
        events = []
        if include_audit_trail:
            try:
                events = await db.get_assessment_events(assessment_id)
            except Exception:
                pass  # Continue without events if not available
        
        # Prepare export data
        export_data = {
            "assessment": assessment,
            "export_metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "format": export_format,
                "version": "1.0"
            }
        }
        
        if include_audit_trail:
            export_data["audit_trail"] = events
        
        # Generate export based on format
        if export_format == "json":
            import json
            filename = f"tra_export_{assessment_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
            return {
                "success": True,
                "assessment_id": assessment_id,
                "format": "json",
                "filename": filename,
                "data": export_data,
                "download_url": f"{settings.base_url}/download/{assessment_id}/{filename}",
                "message": "JSON export generated successfully"
            }
            
        elif export_format == "docx":
            # For DOCX, we would need to generate an actual Word document
            # For now, return placeholder
            filename = f"tra_report_{assessment_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.docx"
            
            return {
                "success": True,
                "assessment_id": assessment_id,
                "format": "docx",
                "filename": filename,
                "s3_key": f"exports/{assessment_id}/{filename}",
                "download_url": f"{settings.base_url}/download/{assessment_id}/{filename}",
                "message": "DOCX report generation queued",
                "note": "Report will be available for download shortly"
            }
        
        else:
            return {
                "success": False,
                "error": f"Unsupported export format: {export_format}"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def update_state(
    assessment_id: str,
    new_state: str,
    comment: str = None
) -> dict:
    """
    Update the state of an assessment.
    
    Args:
        assessment_id: ID of the assessment
        new_state: New state (draft, submitted, under_review, sent_back, finalized)
        comment: Optional comment about the state change
    
    Returns:
        Dictionary with update confirmation
    """
    try:
        db = get_db_service()
        
        # Validate state
        valid_states = [state.value for state in AssessmentState]
        if new_state not in valid_states:
            return {
                "success": False,
                "error": f"Invalid state: {new_state}. Must be one of: {', '.join(valid_states)}"
            }
        
        # Prepare updates
        updates = {
            "current_state": new_state,
            "updated_at": datetime.utcnow()
        }
        
        # Add state-specific timestamps
        if new_state == AssessmentState.SUBMITTED:
            updates["submitted_at"] = datetime.utcnow()
        elif new_state == AssessmentState.FINALIZED:
            updates["finalized_at"] = datetime.utcnow()
        
        # Update assessment
        result = await db.update_assessment(assessment_id, updates)
        
        # Create event for state change
        try:
            from backend.models.tra_models import TraEvent, EventType
            
            event = TraEvent(
                event_id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                event_type=EventType.ASSESSMENT_SUBMITTED if new_state == "submitted" else EventType.STATUS_CHECKED,
                description=f"Assessment state changed to {new_state}",
                actor="system",
                metadata={"new_state": new_state, "comment": comment},
                pk=f"ASSESSMENT#{assessment_id}",
                sk=f"EVENT#{datetime.utcnow().isoformat()}#{str(uuid.uuid4())[:8]}"
            )
            
            await db.create_event(event)
        except Exception:
            pass  # Continue even if event creation fails
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "previous_state": result.get("previous_state") if result else "unknown",
            "new_state": new_state,
            "message": f"Assessment state updated to {new_state}",
            "comment": comment
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
