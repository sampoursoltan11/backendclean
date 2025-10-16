
"""
FastAPI Application - Strands 1.x Native TRA System
Provides WebSocket endpoints for Simple and Enhanced TRA variants
"""

import json
import logging
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from decimal import Decimal
from websockets.exceptions import ConnectionClosedError

from backend.core.config import get_settings
from backend.utils.common import serialize_datetime

# Set up logging (try file logging, fall back to console only)
try:
    from backend.logging_config import setup_logging
    log_file = setup_logging('logs/tra_system.log')
    print(f"📝 All logs are being saved to: {log_file}")
except Exception as e:
    # If file logging fails (e.g., on AWS EB), just use console logging
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    print(f"📝 Using console logging only (file logging unavailable): {e}")

from backend.variants.enterprise import create_enterprise_agent
from backend.services.s3_service import S3Service
from backend.services.bedrock_kb_service import BedrockKnowledgeBaseService
from backend.services.dynamodb_service import DynamoDBService
from backend.services.file_tracking_service import FileTrackingService

logger = logging.getLogger(__name__)

app = FastAPI(title="TRA System API", version="2.0.0")

# Alias for backward compatibility
_serialize_datetimes = serialize_datetime

# Health check endpoint for AWS Elastic Beanstalk and monitoring
@app.get("/api/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {
        "status": "healthy",
        "service": "TRA System API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Mount static files for frontend assets (CSS, JS, etc.)
import os
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "build")
if os.path.exists(frontend_path):
    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# Serve frontend HTML at root path
@app.get("/")
async def root():
    """Serve the frontend application"""
    frontend_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "build", "enterprise_tra_home_clean.html")
    if os.path.exists(frontend_file):
        return FileResponse(frontend_file)
    else:
        return {
            "message": "BHP Technology & Application Services Assessment API",
            "status": "online",
            "version": "2.0.0",
            "note": "Frontend not found - API only mode"
        }

@app.get("/api/documents/ingestion_status/{ingestion_job_id}")
async def get_ingestion_status(ingestion_job_id: str):
    kb = get_kb()
    status = await kb.check_ingestion_status(ingestion_job_id)
    status = _serialize_datetimes(status)
    # Always return top-level 'ready' and 'complete' flags for frontend polling
    response = dict(status)
    # For compatibility, add 'ready' and 'complete' at the top level
    response['ready'] = bool(status.get('is_ready', False))
    response['complete'] = bool(status.get('is_complete', False))
    logger.debug(f"Ingestion status for job {ingestion_job_id}: status={status.get('status')}, is_ready={status.get('is_ready')}, is_complete={status.get('is_complete')}")
    return JSONResponse(response)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Singleton services
_s3: Optional[S3Service] = None
_kb: Optional[BedrockKnowledgeBaseService] = None
_db: Optional[DynamoDBService] = None
_file_tracker: Optional[FileTrackingService] = None


def get_s3() -> S3Service:
    global _s3
    if _s3 is None:
        _s3 = S3Service()
    return _s3


def get_kb() -> BedrockKnowledgeBaseService:
    global _kb
    if _kb is None:
        _kb = BedrockKnowledgeBaseService()
    return _kb


def get_db() -> DynamoDBService:
    global _db
    if _db is None:
        _db = DynamoDBService()
    return _db


def get_file_tracker() -> FileTrackingService:
    global _file_tracker
    if _file_tracker is None:
        _file_tracker = FileTrackingService()
    return _file_tracker






@app.websocket("/ws/enterprise/{session_id}")
async def enterprise_tra_websocket(websocket: WebSocket, session_id: str):
    """
    Enterprise TRA WebSocket - Multi-agent architecture with intelligent routing
    Uses Strands 1.x native orchestration: Orchestrator + 4 Specialized Agents
    """
    await websocket.accept()
    
    try:
        # Create Enterprise TRA orchestrator
        tra_orchestrator = create_enterprise_agent(session_id)
        logger.info(f"Enterprise TRA orchestrator initialized for session: {session_id}")
        # Persistent context dict for this WebSocket session
        persistent_context = {}
    except Exception as e:
        logger.error(f"Failed to initialize Enterprise TRA: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Initialization error: {str(e)}"
        }))
        await websocket.close()
        return
    
    async def safe_send(data: dict):
        try:
            if websocket.client_state.value == 1:  # CONNECTED
                await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.warning(f"WebSocket send failed: {e}")
    
    while True:
        logger.debug("WebSocket waiting for client message...")
        try:
            data = await websocket.receive_text()
            logger.debug(f"WebSocket received: {data[:100]}...")  # Log first 100 chars
        except Exception as e:
            logger.debug(f"WebSocket receive exception: {e}")
            break
        try:
            payload = json.loads(data)
        except Exception:
            logger.warning(f"WebSocket received invalid JSON: {data[:100]}...")
            await safe_send({"type": "error", "message": "Invalid JSON"})
            continue
        if payload.get('type') == 'message':
            message = payload.get('content', '')
            # Merge incoming context into persistent_context, with incoming taking precedence
            incoming_context = payload.get('context', {})
            if incoming_context:
                persistent_context.update(incoming_context)
            logger.debug(f"Routing to orchestrator: message='{message[:50]}...', context_keys={list(persistent_context.keys())}")
            response = await tra_orchestrator.invoke_async(message, persistent_context)
            # IMPORTANT: The orchestrator updates persistent_context in place
            # No need to re-assign since Python dicts are mutable and passed by reference
            logger.debug(f"Orchestrator response received, context updated with keys: {list(persistent_context.keys())}")
            logger.debug(f"Sending response to client: {response[:100]}...")
            # Send back updated context for client-side state preservation
            # Serialize datetime objects before sending
            try:
                serialized_context = _serialize_datetimes(persistent_context)
                await websocket.send_json({"type": "message", "content": response, "context": serialized_context})
            except Exception as e:
                logger.error(f"WebSocket send_json exception: {e}", exc_info=True)
                break

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    assessment_id: str = Form(...),
    project_name: Optional[str] = Form(None)
):
    """Upload document, generate AI summary, and save to DynamoDB (No KB upload - faster!)."""
    try:
        logger.debug(f"Upload: Received upload: filename={file.filename}, session_id={session_id}, assessment_id={assessment_id}")
        s3 = get_s3()
        db = get_db()
        
        content = await file.read()
        logger.debug(f"Upload: File size: {len(content)} bytes")
        
        # Generate unique document ID
        import uuid
        document_id = str(uuid.uuid4())
        s3_key = f"documents/{assessment_id}/{document_id}/{file.filename}"
        
        # Upload to S3
        s3_result = await s3.upload_file(content, s3_key)
        logger.debug(f"Upload: S3 upload result: {s3_result}")
        
        if not s3_result.get('success'):
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "S3 upload failed",
                    "message": "Failed to upload document to storage"
                }
            )
        
        # Extract text and generate summary
        try:
            # Determine file type and extract text
            file_extension = file.filename.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                # Extract text from PDF
                import io
                from PyPDF2 import PdfReader
                
                pdf_file = io.BytesIO(content)
                pdf_reader = PdfReader(pdf_file)
                
                # Extract text from first 10 pages
                file_text = ""
                for page in pdf_reader.pages[:10]:
                    file_text += page.extract_text()
                
                # Limit to 4000 characters
                file_text = file_text[:4000]
                logger.debug(f"Upload: Extracted {len(file_text)} chars from PDF")
                
            elif file_extension == 'docx':
                # Extract text from DOCX
                import io
                from docx import Document
                
                doc = Document(io.BytesIO(content))
                file_text = "\n".join([para.text for para in doc.paragraphs])
                
                # Limit to 4000 characters
                file_text = file_text[:4000]
                logger.debug(f"Upload: Extracted {len(file_text)} chars from DOCX")
                
            elif file_extension in ['txt', 'md', 'json', 'csv']:
                # Plain text files
                file_text = content.decode('utf-8', errors='ignore')[:4000]
                logger.debug(f"Upload: Extracted {len(file_text)} chars from text file")
            else:
                # Unsupported file type
                file_text = f"Document: {file.filename}"
                logger.debug(f"Upload: Unsupported file type: {file_extension}")
            
            # Generate AI summary
            from backend.tools.document_tools import generate_document_summary
            summary_result = await generate_document_summary(file_text, file.filename)
            
            summary = summary_result.get('summary', f'Document: {file.filename}')
            key_topics = summary_result.get('key_topics', [])
            
            logger.debug(f"Upload: Summary generated: {summary[:100]}...")
            
        except Exception as e:
            logger.debug(f"Upload: Text extraction error: {e}")
            import traceback
            traceback.print_exc()
            summary = f"Document uploaded: {file.filename}"
            key_topics = []
        
        # Check if document with same name already exists
        existing_docs = await db.get_documents_by_assessment(assessment_id)
        existing_doc = next(
            (doc for doc in existing_docs if doc.get('filename') == file.filename),
            None
        )
        
        if existing_doc:
            # UPDATE: Replace existing summary
            await db.update_document_summary(
                existing_doc['document_id'],
                summary,
                key_topics
            )
            message = f"✅ Updated document '{file.filename}' with new AI summary"
            logger.debug(f"Upload: Updated existing document")
        else:
            # CREATE: New document record
            await db.create_document_record(
                document_id=document_id,
                assessment_id=assessment_id,
                filename=file.filename,
                file_size=len(content),
                content_type=file.content_type or 'application/octet-stream',
                s3_key=s3_key,
                summary=summary,
                key_topics=key_topics,
                session_id=session_id
            )
            message = f"✅ Uploaded '{file.filename}' - AI summary ready!"
            logger.debug(f"Upload: Created new document record")
        
        # Update assessment's linked documents list
        await db.update_assessment_documents_list(assessment_id)
        
        # NEW: Auto-trigger risk area analysis for ALL document uploads
        logger.info(f"Auto-analysis: Starting auto-analysis for assessment {assessment_id}")
        try:
            # Trigger automatic risk area analysis
            from backend.tools.document_tools import suggest_risk_areas_from_documents
            from backend.tools.question_tools import get_decision_tree
            
            logger.info(f"Auto-analysis: Calling suggest_risk_areas_from_documents...")
            suggestions = await suggest_risk_areas_from_documents(assessment_id)
            logger.info(f"Auto-analysis: Suggestions result: {suggestions}")
            
            if suggestions.get('success') and suggestions.get('suggested_risk_areas'):
                logger.info(f"Auto-analysis: Found {len(suggestions['suggested_risk_areas'])} suggested areas")
                
                # Map risk area names to IDs
                decision_tree = get_decision_tree()
                # Handle both dict format (decision_tree2.yaml) and list format
                risk_areas_raw = decision_tree.get('risk_areas', {})
                if isinstance(risk_areas_raw, dict):
                    # decision_tree2.yaml format: dict with keys like 'third_party'
                    risk_area_map = {area_data.get('name', area_id): area_id for area_id, area_data in risk_areas_raw.items()}
                else:
                    # decision_tree.yaml format: list of dicts
                    risk_area_map = {ra['name']: ra['id'] for ra in risk_areas_raw}
                logger.info(f"Auto-analysis: Risk area map: {risk_area_map}")
                
                risk_area_ids = []
                for area_name in suggestions['suggested_risk_areas']:
                    area_id = risk_area_map.get(area_name)
                    if area_id:
                        risk_area_ids.append(area_id)
                        logger.info(f"Auto-analysis: Mapped {area_name} -> {area_id}")
                    else:
                        logger.info(f"Auto-analysis: Could not map {area_name}")
                
                if risk_area_ids:
                    logger.info(f"[AUTO-ANALYSIS] Risk area IDs to add: {risk_area_ids}")

                    # Add all risk areas at once atomically to avoid race conditions
                    from backend.services.dynamodb_service import DynamoDBService
                    db = DynamoDBService()
                    assessment = await db.get_assessment(assessment_id)
                    existing_areas = set(assessment.get('active_risk_areas', []))
                    logger.info(f"[AUTO-ANALYSIS] Existing areas: {existing_areas}")

                    # Merge with existing areas and add all new ones
                    for risk_area_id in risk_area_ids:
                        if risk_area_id not in existing_areas:
                            existing_areas.add(risk_area_id)
                            logger.info(f"[AUTO-ANALYSIS] Added to set: {risk_area_id}")

                    # Single atomic update with all risk areas
                    final_list = list(existing_areas)
                    logger.info(f"[AUTO-ANALYSIS] Final list to save: {final_list}")
                    await db.update_assessment(assessment_id, {"active_risk_areas": final_list})
                    logger.info(f"[AUTO-ANALYSIS] Update complete")

                    # CRITICAL: Verify what was actually saved - ONLY use verified data
                    verified_assessment = await db.get_assessment(assessment_id)
                    verified_risk_areas = verified_assessment.get('active_risk_areas', [])
                    logger.info(f"[AUTO-ANALYSIS] Verified in DB: {verified_risk_areas}")

                    # Map IDs back to names for display using ONLY what's in DB
                    decision_tree = get_decision_tree()
                    risk_areas_raw = decision_tree.get('risk_areas', {})
                    if isinstance(risk_areas_raw, dict):
                        id_to_name_map = {area_id: area_data.get('name', area_id) for area_id, area_data in risk_areas_raw.items()}
                    else:
                        id_to_name_map = {ra['id']: ra['name'] for ra in risk_areas_raw}

                    verified_area_names = [id_to_name_map.get(area_id, area_id) for area_id in verified_risk_areas]
                    logger.info(f"[AUTO-ANALYSIS] Verified area names: {verified_area_names}")

                    logger.info(f"Auto-analysis: Returning auto-analysis success response")
                    return JSONResponse({
                        "success": True,
                        "file_id": document_id,
                        "s3_key": s3_key,
                        "summary": summary,
                        "key_topics": key_topics,
                        "word_count": summary_result.get('word_count', 0),
                        "message": f"✅ Document analyzed! Added {len(verified_risk_areas)} risk areas to your TRA: {', '.join(verified_area_names)}",
                        "auto_analyzed": True,
                        "risk_areas_added": verified_area_names,
                        "upload_status": {
                            "s3": True,
                            "summary_generated": True,
                            "saved_to_db": True,
                            "risk_analysis": True
                        }
                    })
                else:
                    logger.info(f"Auto-analysis: No risk area IDs mapped")
            else:
                logger.info(f"Auto-analysis: No suggestions or analysis failed: {suggestions}")
                
        except Exception as e:
            logger.info(f"Auto-analysis: Exception in auto-analysis: {e}")
            import traceback
            traceback.print_exc()
        
        # Standard response (no auto-analysis)
        return JSONResponse({
            "success": True,
            "file_id": document_id,
            "s3_key": s3_key,
            "summary": summary,
            "key_topics": key_topics,
            "word_count": summary_result.get('word_count', 0),
            "message": message,
            "upload_status": {
                "s3": True,
                "summary_generated": True,
                "saved_to_db": True
            }
        })
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/session/{session_id}")
async def list_session_documents(session_id: str):
    """List documents for a session."""
    try:
        file_tracker = get_file_tracker()
        files = await file_tracker.get_session_files(session_id)
        
        return JSONResponse({
            "success": True,
            "session_id": session_id,
            "files": files,
            "count": len(files)
        })
        
    except Exception as e:
        logger.error(f"List files failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/status")
async def system_status():
    """Get system status and capabilities."""
    return JSONResponse({
        "system": "TRA System",
        "version": "2.0.0",
        "framework": "Strands Agents 1.x",
        "orchestrator": {
            "endpoint": "/ws/enterprise/{session_id}",
            "description": "Enterprise orchestrator (Strands-agents 1.x)",
            "agents": 4,
            "architecture": "orchestrator + agents",
            "pattern": "intelligent_routing",
            "status": "production"
        },
        "features": [
            "Assessment Lifecycle Management",
            "Document Processing & RAG",
            "Risk Area Suggestions",
            "Dynamic Questionnaire Flow",
            "Real-Time Collaboration",
            "Export & Reporting",
            "Observability & Analytics"
        ]
    })


@app.get("/api/assessments/search")
async def search_assessments(query: str, limit: int = 3):
    """Search assessments by project name/title and return top 3 results sorted by last updated."""
    try:
        db = get_db()
        
        if not query or not query.strip():
            return JSONResponse({
                "success": True,
                "assessments": [],
                "count": 0,
                "message": "Empty query"
            })
        
        # Call the search method
        results = await db.search_assessments(query.strip(), limit)
        
        # Serialize the results for JSON response
        serialized_results = _serialize_datetimes(results)
        
        return JSONResponse({
            "success": True,
            "assessments": serialized_results,
            "count": len(serialized_results)
        })
        
    except Exception as e:
        logger.error(f"Assessment search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/assessments/{assessment_id}")
async def get_assessment_details(assessment_id: str):
    """
    Validate TRA ID and return basic assessment details.
    Used by frontend to validate TRA ID before document upload.
    """
    try:
        db = get_db()
        
        # Get assessment from DynamoDB
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "TRA ID not found"
                }
            )
        
        # Serialize and return basic details
        serialized = _serialize_datetimes(assessment)
        
        return JSONResponse({
            "success": True,
            "assessment_id": serialized.get('assessment_id', assessment_id),
            "title": serialized.get('title', 'Untitled Assessment'),
            "status": serialized.get('current_state', 'draft'),
            "completion": serialized.get('completion_percentage', 0)
        })
        
    except Exception as e:
        logger.error(f"Assessment validation failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/assessments/{assessment_id}/documents")
async def get_assessment_documents(assessment_id: str):
    """
    Get all documents and their summaries for a specific TRA assessment.
    Returns document metadata including DynamoDB summaries.
    """
    try:
        db = get_db()

        # Verify assessment exists
        assessment = await db.get_assessment(assessment_id)
        if not assessment:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": f"TRA ID {assessment_id} not found"
                }
            )

        # Get documents for this assessment
        documents = await db.get_documents_by_assessment(assessment_id)

        # Format document summaries for frontend
        document_summaries = []
        for doc in documents:
            doc_info = {
                "document_id": doc.get('document_id', ''),
                "filename": doc.get('filename', 'Unknown'),
                "file_size": doc.get('file_size', 0),
                "upload_date": doc.get('created_at', ''),
                "content_summary": doc.get('content_summary', 'No summary available'),
                "key_topics": doc.get('tags', []),
                "word_count": len(doc.get('content_summary', '').split()) if doc.get('content_summary') else 0
            }
            document_summaries.append(doc_info)

        # Serialize timestamps
        serialized_docs = _serialize_datetimes(document_summaries)

        return JSONResponse({
            "success": True,
            "assessment_id": assessment_id,
            "assessment_title": assessment.get('title', 'Untitled Assessment'),
            "document_count": len(document_summaries),
            "documents": serialized_docs,
            "message": f"Found {len(document_summaries)} document(s) for TRA {assessment_id}"
        })

    except Exception as e:
        logger.error(f"Get assessment documents failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/assessments/{assessment_id}/progress")
async def get_assessment_progress_api(assessment_id: str):
    """
    Get progress breakdown for an assessment, including per-risk-area completion.
    Used by frontend to display progress bars during question answering.
    """
    try:
        from backend.tools.status_tools import get_assessment_summary

        # Call the existing tool function
        result = await get_assessment_summary(assessment_id)

        if not result.get('success'):
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": result.get('error', 'Assessment not found')
                }
            )

        # Serialize timestamps
        serialized_result = _serialize_datetimes(result)

        return JSONResponse(serialized_result)

    except Exception as e:
        logger.error(f"Get assessment progress failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
