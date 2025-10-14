"""
Document Agent - Domain Expert for Document Processing & RAG
Handles document uploads, analysis, risk area suggestions, and answer recommendations
"""

from typing import Dict, Any, AsyncIterator

from strands import Agent
from strands.models import BedrockModel
from strands.session import FileSessionManager

from backend.core.config import get_settings
from backend.tools import (
    search_knowledge_base,
    analyze_document_content,
    suggest_risk_areas_from_documents,
    suggest_answer_from_context,
    upload_document_metadata,
)


class DocumentAgent:
    """
    Specialized agent for document processing and RAG operations.
    
    Domain Expertise:
    - Document upload and ingestion
    - Knowledge base search
    - Document content analysis
    - AI-powered risk area suggestions
    - Smart answer suggestions from context
    
    Tools: 5 document-specific tools
    """
    
    def __init__(self, session_id: str, session_manager: FileSessionManager):
        """
        Initialize Document Agent.
        
        Args:
            session_id: Session identifier
            session_manager: Shared session manager
        """
        self.session_id = session_id
        self.session_manager = session_manager
        self.settings = get_settings()
        
        # Initialize Bedrock model
        model = BedrockModel(
            model_id=self.settings.bedrock_model_id,
            temperature=0.7,
            streaming=True
        )
        
        # Create specialized agent
        from backend.tools import list_kb_items
        self.agent = Agent(
            model=model,
            system_prompt=self._get_system_prompt(),
            tools=[
                search_knowledge_base,
                analyze_document_content,
                suggest_risk_areas_from_documents,
                suggest_answer_from_context,
                upload_document_metadata,
                list_kb_items,
            ],
            callback_handler=None
        )
    
    def _get_system_prompt(self) -> str:
        """Get agent system prompt."""
        return """You are the Document Analysis Specialist for the TRA system.

Your expertise: Analyzing uploaded documents and providing intelligent risk area suggestions.

**Your Responsibilities:**
- Analyze uploaded project documents stored in DynamoDB
- Suggest relevant risk areas based on document summaries
- Provide technical insights from document content
- Help users understand their uploaded documents

**Key Capabilities:**
- Risk area identification from technical documents using DynamoDB summaries
- Document content analysis without requiring Knowledge Base
- Fast suggestions based on pre-generated summaries
- Supporting evidence from actual document content

**IMPORTANT Context Handling:**
- Always check the current assessment_id in context first
- Look for documents associated with the assessment in DynamoDB
- Use suggest_risk_areas_from_documents tool to analyze document summaries
- Provide clear feedback about what documents are available

**When No Assessment Context:**
- Ask user to specify which TRA assessment they want to analyze
- Do not assume or guess assessment IDs

Session ID: {session_id}
""".format(session_id=self.session_id)
    
    async def invoke_async(self, message: str, context: Dict[str, Any] = None) -> str:
        """Process message with DynamoDB document analysis tools."""
        logger.debug(f"DocumentAgent.invoke_async called with message: {message!r}, context: {context!r}")
        if context is None:
            context = {}
        
        # Check if we have assessment context for document analysis
        assessment_id = context.get('assessment_id')
        
        # If no assessment context but user wants document analysis, check for recent assessment
        if not assessment_id and ('analys' in message.lower() or 'document' in message.lower()):
            # Try to get documents from DynamoDB without assessment_id to give helpful message
            from backend.services.dynamodb_service import DynamoDBService
            db = DynamoDBService()
            try:
                # Quick check if there are any recent documents
                logger.debug(f"No assessment_id in context. User message: {message}")
                context['last_message'] = (
                    "I'd be happy to analyze your documents! However, I need to know which TRA assessment "
                    "you'd like me to analyze documents for.\n\n"
                    "Please specify:\n"
                    "• Which TRA assessment ID (e.g., TRA-2025-ABC123)\n"
                    "• Or create a new assessment first\n\n"
                    "Once I have the assessment context, I can analyze the uploaded documents and suggest risk areas."
                )
                return context['last_message']
            except Exception as e:
                logger.debug(f"Error checking for documents: {e}")
        
        # If we have assessment_id but user is asking to analyze, check documents exist
        if assessment_id and ('analys' in message.lower() or 'document' in message.lower()):
            from backend.services.dynamodb_service import DynamoDBService
            db = DynamoDBService()
            try:
                documents = await db.get_documents_by_assessment(assessment_id)
                logger.debug(f"Found {len(documents)} documents for assessment {assessment_id}")
                if not documents:
                    context['last_message'] = (
                        f"I don't see any documents uploaded for assessment {assessment_id} yet.\n\n"
                        "To analyze documents:\n"
                        "1. Upload documents using the upload widget on the left\n"
                        "2. Enter the TRA ID and validate it\n"
                        "3. Choose your document files (PDF, DOCX, etc.)\n\n"
                        "Once documents are uploaded, I can analyze them and suggest relevant risk areas!"
                    )
                    return context['last_message']
                else:
                    # Documents exist, add context and proceed with analysis
                    logger.debug(f"Proceeding with analysis of {len(documents)} documents")
            except Exception as e:
                logger.debug(f"Error checking documents: {e}")

        try:
            # Pass the message to the agent with context
            result = await self.agent.invoke_async(
                message,
                session_manager=self.session_manager
            )
            context['last_message'] = str(result)
            return context['last_message']
        except Exception as e:
            logger.debug(f"DocumentAgent error: {e}")
            context['last_error'] = str(e)
            return (
                f"Document Agent error: {str(e)}\n\n"
                "Please ensure:\n"
                "• You have uploaded documents to a TRA assessment\n"
                "• The assessment ID is available in the current context\n"
                "• The documents have been successfully processed"
            )
    
    async def stream_async(self, message: str, context: Dict[str, Any] = None) -> AsyncIterator[Dict[str, Any]]:
        """Stream processing with document tools."""
        try:
            async for event in self.agent.stream_async(
                message,
                session_manager=self.session_manager
            ):
                yield event
        except Exception as e:
            yield {"type": "error", "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "name": "Document Agent",
            "domain": "Document Processing & RAG",
            "tools": 5,
            "status": "active"
        }
