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
When user requests "review my answers" or "review answers for [TRA-ID]":

STEP 1: CALL review_answers(assessment_id) tool
STEP 2: WAIT for tool response
STEP 3: USE ONLY the data from the tool response - DO NOT MAKE UP DATA

The review_answers tool returns:
- assessment_id (TRA ID)
- title (Project name)
- completion_percentage
- review_data: array of risk areas with qa_pairs

STEP 4: Format response EXACTLY like this, using tool data:

"[EDITABLE_REVIEW]
**Assessment Review: [USE tool.assessment_id]**
**Project:** [USE tool.title]
**Overall Progress:** [USE tool.completion_percentage]% complete

**Answers by Risk Area:**

[FOR EACH item in tool.review_data]:
**[USE item.risk_area]:** [USE item.questions_answered]/[USE item.total_questions] questions answered
[FOR EACH qa in item.qa_pairs]:
• **Q ([USE qa.question_id]):** [USE qa.question]
  **A:** [USE qa.answer]
[END FOR]
[END FOR]

**Status:** [Current State from DB]
**Next Steps:** [Provide recommendations]"

CRITICAL:
- Show ONLY risk areas returned by the tool (if tool returns 1, show 1)
- Show ONLY questions returned by the tool (if tool returns 8, show 8)
- Use EXACT question text from qa.question field
- Use EXACT answer text from qa.answer field
- DO NOT invent or hallucinate any data

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

**CRITICAL RULES - YOU MUST FOLLOW THESE:**
1. **NEVER hallucinate data** - Use ONLY the exact data returned by the review_answers tool
2. **NEVER invent** risk areas, questions, or answers - Display ONLY what the tool returns
3. **ALWAYS start with [EDITABLE_REVIEW] marker** when showing review answers
4. **USE EXACT VALUES** from tool output:
   - assessment_id (TRA ID)
   - title (Project name)
   - completion_percentage
   - review_data array (risk areas, questions, answers)
5. **DO NOT modify, summarize, or reformat** the data from the tool
6. **If tool returns 1 risk area, show 1 risk area** - not multiple
7. **If tool returns 8/8 questions, show 8/8** - not different numbers

**IMPORTANT:**
- When reviewing answers, structure the output clearly with proper headings and bullet points for readability
- The current assessment ID will be provided in the user's message as "Current assessment ID from context: TRA-XXXX-XXXXXX"
- Use this assessment ID when calling tools like review_answers(), update_state(), generate_assessor_link(), etc.
- If no assessment ID is provided in the message or context, ask the user to specify which assessment they want to work with

Session ID: {session_id}
""".format(session_id=self.session_id)
    
    async def invoke_async(self, message: str, context: Dict[str, Any] = None) -> str:
        """Process message with status tools and update shared context."""
        logger.debug(f"StatusAgent.invoke_async called with message: {message!r}, context: {context!r}")
        if context is None:
            context = {}

        # Extract assessment_id from context or message
        import re
        assessment_id = context.get('assessment_id')
        if not assessment_id and isinstance(message, str):
            match = re.search(r"TRA-\d{4}-[A-Z0-9]+", message, re.IGNORECASE)
            if match:
                assessment_id = match.group(0)
                context['assessment_id'] = assessment_id

        # If we have assessment_id, append it to the message so the LLM knows which assessment to work with
        augmented_message = message
        if assessment_id:
            augmented_message = f"{message}\n\nCurrent assessment ID from context: {assessment_id}"
            logger.debug(f"StatusAgent: Augmented message with assessment_id: {assessment_id}")

        try:
            result = await self.agent.invoke_async(
                augmented_message,
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
