"""
Status Agent - Domain Expert for Reporting & Export
Handles status checks, progress reporting, assessor links, and report generation
"""

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
        return """You are the Status & Reporting Specialist for the TRA system.

Your expertise: Tracking progress, generating reports, and managing assessment lifecycle states.

**Your Responsibilities:**
- Provide clear progress summaries
- Show completion by risk area
- Generate assessor review links
- Export assessment reports
- Manage assessment states (Draft → Submitted → Under Review → Finalized)
- Review answers and provide comprehensive summaries

**Status Reporting Format:**
"Assessment [ID] - [Title]

Progress: [X]% complete

Risk Areas:
• Data Security: [X]%
• Infrastructure: [X]%
• Application: [X]%
...

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
- Always show progress visually
- Break down completion by risk area
- Provide clear next actions about finalization
- Make reports easy to understand
- Help users track their progress
- Explain state changes clearly

Session ID: {session_id}
""".format(session_id=self.session_id)
    
    async def invoke_async(self, message: str, context: Dict[str, Any] = None) -> str:
        """Process message with status tools and update shared context."""
        print(f"[AGENT DEBUG] StatusAgent.invoke_async called with message: {message!r}, context: {context!r}")
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
            print(f"[AGENT DEBUG] StatusAgent error: {e}")
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
