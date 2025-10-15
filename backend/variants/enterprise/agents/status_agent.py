"""
Status Agent - Domain Expert for Reporting & Export
Handles status checks, progress reporting, assessor links, and report generation
"""

import logging
from typing import Dict, Any, AsyncIterator

from strands import Agent
from strands.models import BedrockModel
from strands.session import FileSessionManager

from backend.core.config import get_settings
from backend.tools import (
    get_assessment_summary,
    check_status,
    generate_assessor_link,
    export_assessment,
    update_state,
    review_answers,
)

logger = logging.getLogger(__name__)


class StatusAgent:
    """
    Specialized agent for status reporting and export.
    
    Domain Expertise:
    - Assessment progress tracking
    - Status reporting
    - Assessor link generation
    - Report export (JSON, DOCX)
    - State management
    
    Tools: 6 status-specific tools
    """
    
    def __init__(self, session_id: str, session_manager: FileSessionManager):
        """
        Initialize Status Agent.
        
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
                get_assessment_summary,
                check_status,
                review_answers,
                generate_assessor_link,
                export_assessment,
                update_state,
                list_kb_items,
            ],
            callback_handler=None
        )
    
    def _get_system_prompt(self) -> str:
        """Get agent system prompt."""
        return """You are the Status & Reporting Specialist for the TRA (Technology Risk Assessment) system.

Your expertise: Tracking progress, generating reports, and managing assessment lifecycle states.

**Your Responsibilities:**
- Provide clear progress summaries using the review_answers tool
- Show completion percentage by risk area
- Generate assessor review links
- Export assessment reports
- Manage assessment states (Draft → Submitted → Under Review → Finalized)
- Review all answers and provide comprehensive, well-formatted summaries

**Available Risk Areas in TRA System:**
• Third Party Risk - Third-party involvement in solution design/deployment/operations
• Data Privacy Risk - Personal data handling and privacy compliance
• AI Risk - Artificial Intelligence implementation and risks
• IP Risk - Intellectual Property protection and licensing

**Answer Review Format:**
When user requests "review my answers" or "review answers for [TRA-ID]", use the review_answers tool which returns structured data including:
- assessment_id (TRA ID)
- title (Project name)
- completion_percentage
- answers_by_risk_area (organized by risk area with question IDs and answers)

Format the response as a clear, structured summary:
"**Assessment Review: [TRA-ID]**
**Project:** [Title]
**Overall Progress:** [X]% complete

**Answers by Risk Area:**

**Third Party Risk:** [X/Y questions answered]
• Question [ID]: [Answer]
• Question [ID]: [Answer]
...

**Data Privacy Risk:** [X/Y questions answered]
• Question [ID]: [Answer]
...

[Continue for all active risk areas]

**Status:** [Current State]
**Next Steps:** [Recommendations]"

**Status Reporting Format:**
"Assessment [TRA-ID] - [Title]

Overall Progress: [X]% complete

Active Risk Areas:
• Third Party Risk: [Complete/In Progress]
• Data Privacy Risk: [Complete/In Progress]
• AI Risk: [Complete/In Progress]
• IP Risk: [Complete/In Progress]

Current State: [Draft/Submitted/Under Review]
Next Step: [Clear action]"

**Finalization Process:**
When user wants to finalize/submit an assessment:
1. Use update_state tool to change status from "draft" to "submitted"
2. Use generate_assessor_link tool to create review link
3. Explain what happens next:
   - Assessment locked from editing
   - Assessor receives link for review
   - User can track review status

**Key Principles:**
- ALWAYS use review_answers tool when user asks to review answers
- Show progress visually and clearly
- Break down completion by risk area
- Format answers in a readable, organized way
- Provide clear next actions
- Make reports easy to understand
- Help users track their progress
- Explain state changes clearly

**IMPORTANT:** When reviewing answers, structure the output clearly with proper headings and bullet points for readability.

Session ID: {session_id}
""".format(session_id=self.session_id)
    
    async def invoke_async(self, message: str, context: Dict[str, Any] = None) -> str:
        """Process message with status tools and update shared context."""
        logger.debug(f"StatusAgent.invoke_async called with message: {message!r}, context: {context!r}")
        if context is None:
            context = {}
        try:
            result = await self.agent.invoke_async(
                message,
                session_manager=self.session_manager
            )
            context['last_message'] = str(result)
            return context['last_message']
        except Exception as e:
            logger.debug(f"StatusAgent error: {e}")
            context['last_error'] = str(e)
            return f"Status Agent error: {str(e)}"
    
    async def stream_async(self, message: str, context: Dict[str, Any] = None) -> AsyncIterator[Dict[str, Any]]:
        """Stream processing with status tools."""
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
            "name": "Status Agent",
            "domain": "Reporting & Export",
            "tools": 6,
            "status": "active"
        }
