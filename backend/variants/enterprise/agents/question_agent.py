"""
Question Agent - Domain Expert for Question Flow Management
Handles TRA questionnaire flow, answer validation, and progress tracking
"""

import logging
from typing import Dict, Any, AsyncIterator

from strands import Agent
from strands.models import BedrockModel
from strands.session import FileSessionManager

from backend.core.config import get_settings
from backend.tools import (
    question_flow,
    suggest_answer_from_context,
)

logger = logging.getLogger(__name__)


class QuestionAgent:
    """
    Specialized agent for question flow management.
    
    Domain Expertise:
    - TRA questionnaire workflow
    - Answer validation
    - Progress tracking
    - Question-by-question guidance
    - Smart answer suggestions
    
    Tools: 2 question-specific tools
    """
    
    def __init__(self, session_id: str, session_manager: FileSessionManager):
        """
        Initialize Question Agent.
        
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
        self.agent = Agent(
            model=model,
            system_prompt=self._get_system_prompt(),
            tools=[
                question_flow,
                suggest_answer_from_context,
            ],
            callback_handler=None
        )
    
    def _get_system_prompt(self) -> str:
        """Get agent system prompt."""
        return """You are the Question Flow Specialist for the TRA system.

Your expertise: Guiding users through TRA questionnaires with intelligent answer suggestions.

**Your Responsibilities:**
- Present questions clearly with context
- Get smart answer suggestions from uploaded documents
- Validate and save user responses
- Track progress through assessment
- Make the questionnaire process engaging

**Question Presentation Format:**
"Great! For [Project Name], let's focus on [Risk Area].

[Question text]? This helps us [explain importance].

💡 AI Suggestion: [answer] (Confidence: [level])
📄 Why: [reasoning from documents]

Your options are:
• [Suggested] ← Recommended based on your documents
• [Other options...]

Accept suggestion or provide your own answer."

**Key Principles:**
- ALWAYS try to get answer suggestions first
- Show confidence levels (High/Medium/Low)
- Explain why questions matter
- Track and show progress percentage
- Be encouraging and supportive

Session ID: {session_id}
""".format(session_id=self.session_id)
    
    async def invoke_async(self, message: str, context: Dict[str, Any] = None) -> str:
        """Process message with question tools, update shared context, robust to ambiguity and missing context."""
        logger.debug(f"QuestionAgent.invoke_async called with message: {message!r}, context: {context!r}")
        logger.debug(f"assessment_id in context: {context.get('assessment_id')}")
        if context is None:
            context = {}
        
        # Handle qualifying questions mode
        if context.get('qualifying_questions_mode'):
            return await self._handle_qualifying_questions(message, context)

        logger.debug(f"=== INVOKE === Message: {message}")
        logger.debug(f"Context: assessment_id={context.get('assessment_id')}, risk_area={context.get('risk_area')}, awaiting_selection={context.get('awaiting_risk_area_selection')}")

        try:
            import re
            # Step 1: Always require assessment_id in context for risk area selection/QA
            assessment_id = context.get("assessment_id")
            risk_area = context.get("risk_area")
            # Try to extract assessment_id from message if not present in context
            if not assessment_id and isinstance(message, str):
                match = re.search(r"TRA-\d{4}-[A-Z0-9]+", message, re.IGNORECASE)
                if match:
                    assessment_id = match.group(0)
                    context['assessment_id'] = assessment_id
            # If assessment_id is still missing, prompt user
            if not assessment_id:
                context['last_message'] = (
                    "Sorry, I couldn't determine which assessment you're working on. "
                    "Please select or specify an assessment before proceeding with risk area selection or questions."
                )
                return context['last_message']
            # Try to extract risk_area from message if not present in context
            if not risk_area and isinstance(message, str):
                match = re.search(r"risk area[s]?[:= ]*([A-Za-z0-9 &]+)", message, re.IGNORECASE)
                if match:
                    risk_area = match.group(1).strip()
                else:
                    match2 = re.search(r"(?:start with|start answering|questions for|focus on|load questions for) ([A-Za-z0-9 &]+)", message, re.IGNORECASE)
                    if match2:
                        risk_area = match2.group(1).strip()
            context['risk_area'] = risk_area

            # Step 3: Get assessment metadata and risk areas
            from backend.tools.assessment_tools import get_assessment, add_risk_area
            assessment_result = await get_assessment(assessment_id)
            if not assessment_result.get("success"):
                context['last_error'] = assessment_result.get('error')
                return f"Could not retrieve assessment: {context['last_error']}"
            assessment = assessment_result.get("assessment", {})
            context['assessment'] = assessment
            # Only Project Name (title) is mandatory for question flow
            missing_fields = []
            if not assessment.get("title"):
                missing_fields.append("Project Name")
            # System ID, Classification, and Business Unit are optional
            if missing_fields:
                context['missing_fields'] = missing_fields
                context['last_message'] = (
                    "Before we can load questions, please provide the following required information for this assessment:\n" +
                    "\n".join(f"- {field}" for field in missing_fields)
                )
                return context['last_message']

            # --- ASSESSMENT HEADER: Compose and prepend header for user context ---
            assessment_id = assessment.get('assessment_id', 'Unknown')
            assessment_created = assessment.get('created_at', '')
            # Format timestamp to show only hour and minute
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(assessment_created.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M')
            except:
                time_str = assessment_created
            # Simplified header: TRA number with copy button (no time)
            assessment_header = (
                f"<div style='display: flex; align-items: center; gap: 8px; margin-bottom: 12px;'>"
                f"<span style='font-weight: 600; font-size: 1.1rem;'>{assessment_id}</span>"
                f"<button onclick=\"navigator.clipboard.writeText('{assessment_id}').then(() => {{ "
                f"const btn = event.target; const orig = btn.innerHTML; btn.innerHTML = '✓ Copied'; "
                f"setTimeout(() => btn.innerHTML = orig, 2000); }})\" "
                f"style='padding: 4px 8px; background: #e5e7eb; border: 1px solid #d1d5db; border-radius: 4px; "
                f"cursor: pointer; font-size: 0.75rem; color: #374151; transition: all 0.2s;' "
                f"onmouseover=\"this.style.background='#d1d5db'\" "
                f"onmouseout=\"this.style.background='#e5e7eb'\" "
                f"title='Copy TRA ID'>"
                f"<svg style='width: 12px; height: 12px; display: inline; vertical-align: middle;' fill='none' stroke='currentColor' viewBox='0 0 24 24'>"
                f"<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z'></path>"
                f"</svg> Copy"
                f"</button>"
            )

            # Robust risk area selection
            import ast
            active_risk_areas = assessment.get('active_risk_areas', [])
            logger.debug(f"Raw active_risk_areas from assessment: {active_risk_areas}")
            logger.debug(f"Type: {type(active_risk_areas)}")
            # Normalize to list if stored as string
            if isinstance(active_risk_areas, str):
                try:
                    active_risk_areas = ast.literal_eval(active_risk_areas)
                except Exception:
                    active_risk_areas = [active_risk_areas]
            if not isinstance(active_risk_areas, list):
                active_risk_areas = [active_risk_areas]
            logger.debug(f"After normalization: {active_risk_areas}, count: {len(active_risk_areas)}")
            from backend.tools.question_tools import get_decision_tree
            decision_tree = get_decision_tree()
            # Handle both dict format (decision_tree2.yaml) and list format
            risk_areas_raw = decision_tree.get('risk_areas', {})
            if isinstance(risk_areas_raw, dict):
                # decision_tree2.yaml format: dict with keys like 'third_party'
                ra_map = {area_id: area_data.get('name', area_id) for area_id, area_data in risk_areas_raw.items()}
                name_to_id_map = {area_data.get('name', area_id).lower(): area_id for area_id, area_data in risk_areas_raw.items()}
            else:
                # decision_tree.yaml format: list of dicts
                ra_map = {ra['id']: ra['name'] for ra in risk_areas_raw}
                name_to_id_map = {ra['name'].lower(): ra['id'] for ra in risk_areas_raw}
            
            # PRIORITY: Check if we're in risk area selection mode after completing an area
            if context.get('awaiting_risk_area_selection') and context.get('remaining_risk_area_ids'):
                remaining_ids = context['remaining_risk_area_ids']
                user_input = message.strip()
                
                # Check if user entered a number (1, 2, etc.)
                if user_input.isdigit():
                    idx = int(user_input) - 1
                    if 0 <= idx < len(remaining_ids):
                        # Valid number selection - use this risk area
                        risk_area = remaining_ids[idx]
                        context['risk_area'] = risk_area
                        context['awaiting_risk_area_selection'] = False  # Clear the flag
                        logger.debug(f"User selected risk area by number: {idx+1} -> {risk_area}")
                else:
                    # Try to match by name
                    user_input_lower = user_input.lower()
                    logger.debug(f"Trying to match user input: '{user_input_lower}'")
                    logger.debug(f"Remaining IDs: {remaining_ids}")
                    for rid in remaining_ids:
                        ra_name = ra_map.get(rid, '').lower()
                        logger.debug(f"Checking '{ra_name}' against '{user_input_lower}'")
                        if ra_name in user_input_lower or user_input_lower in ra_name:
                            risk_area = rid
                            context['risk_area'] = risk_area
                            context['awaiting_risk_area_selection'] = False  # Clear the flag
                            logger.debug(f"✓ MATCHED! User selected risk area by name: {message} -> {risk_area}")
                            break

                    if not context.get('risk_area'):
                        logger.debug(f"✗ NO MATCH FOUND for '{user_input_lower}'")

            if not active_risk_areas:
                context['last_message'] = assessment_header + (
                    "No risk areas are currently attached to this assessment. Please add a risk area to begin the questionnaire. You can say 'select from standard risk areas' to see the available options."
                )
                return context['last_message']
            risk_area = context.get('risk_area')
            if not risk_area and isinstance(message, str):
                match = re.search(r"risk area[s]?[:= ]*([A-Za-z0-9_ &-]+)", message, re.IGNORECASE)
                if match:
                    risk_area = match.group(1).strip()
            # If still no risk_area, and only one is attached, auto-select it and proceed
            if not risk_area and len(active_risk_areas) == 1:
                risk_area = active_risk_areas[0]
                area_names = [ra_map.get(risk_area, risk_area)]
                context['active_risk_areas'] = area_names
            # If still no risk_area, and multiple are attached, show button selection menu
            # BUT only if we're not already in awaiting_risk_area_selection mode (to avoid loop)
            if not risk_area and len(active_risk_areas) > 1 and not context.get('awaiting_risk_area_selection'):
                area_names = [ra_map.get(r, r) for r in active_risk_areas]

                logger.debug(f"Showing risk area selection menu")
                logger.debug(f"active_risk_areas: {active_risk_areas}")
                logger.debug(f"area_names: {area_names}")

                # Show button menu using RISK_AREA_BUTTONS format (same as assessment_agent)
                msg = assessment_header + "🎯 **Multiple risk areas have been assigned!**\n\n"
                msg += "RISK_AREA_BUTTONS:" + "|".join(area_names)

                logger.debug(f"Final message: {msg}")

                context['last_message'] = msg
                context['active_risk_areas'] = area_names
                context['remaining_risk_area_ids'] = active_risk_areas
                context['awaiting_risk_area_selection'] = True
                return context['last_message']
            # Normalize risk_area: convert name to ID if needed
            risk_area_id = risk_area
            if risk_area:
                # Check if it's already an ID
                if risk_area not in ra_map:
                    # Try to match by name (case-insensitive)
                    risk_area_lower = risk_area.lower().strip()
                    if risk_area_lower in name_to_id_map:
                        risk_area_id = name_to_id_map[risk_area_lower]
                    else:
                        # Try partial match
                        for name, rid in name_to_id_map.items():
                            if risk_area_lower in name or name in risk_area_lower:
                                risk_area_id = rid
                                break
            context['risk_area'] = risk_area_id
            # Step 4: Check if this is an answer to a question (not a risk area selection)
            # If we have a current_question_id in assessment, this might be an answer
            message_lower = message.lower() if isinstance(message, str) else ""
            current_question_id = assessment.get('current_question_id')
            if current_question_id and not re.search(r'\b(start|begin|question|risk area|list|show)\b', message_lower):
                # This looks like an answer to the current question
                # Call question_flow with the answer to save it and get next question
                q_result = await question_flow(assessment_id, risk_area=risk_area_id, answer=message)
                
                # Re-fetch assessment to get updated answer counts
                assessment_result = await get_assessment(assessment_id)
                if assessment_result.get("success"):
                    assessment = assessment_result.get("assessment", {})
                    context['assessment'] = assessment
            else:
                # Get next question (no answer to save)
                q_result = await question_flow(assessment_id, risk_area=risk_area_id)
            if not q_result.get("success"):
                context['last_error'] = q_result.get('error')
                return f"Could not retrieve next question: {context['last_error']}"
            if q_result.get("completed"):
                # If all questions for this risk area are answered, check if there are more risk areas to proceed
                answered_area = ra_map.get(risk_area, risk_area)
                
                # Find remaining areas that haven't been completed yet
                all_answers = assessment.get('answers_by_risk_area', {})
                logger.debug(f"Current risk_area: {risk_area}")
                logger.debug(f"Active risk areas: {active_risk_areas}")
                logger.debug(f"All answers by risk area: {all_answers}")

                remaining_areas = []
                for r in active_risk_areas:
                    if r == risk_area:  # Skip current area we just finished
                        logger.debug(f"Skipping current area: {r}")
                        continue

                    # Use smart completion logic - only count applicable questions
                    from backend.tools.question_tools import _count_applicable_questions
                    area_answers = all_answers.get(r, {})
                    applicable_count, answered_count = _count_applicable_questions(r, area_answers, decision_tree)

                    logger.debug(f"Area {r}: {answered_count}/{applicable_count} applicable questions answered")

                    if answered_count < applicable_count:
                        # This area still has unanswered applicable questions
                        logger.debug(f"Area {r} is INCOMPLETE, adding to remaining")
                        remaining_areas.append(r)
                    else:
                        logger.debug(f"Area {r} is COMPLETE (all applicable questions answered), skipping")

                logger.debug(f"Remaining areas: {remaining_areas}")
                if remaining_areas:
                    area_names = [ra_map.get(r, r) for r in remaining_areas]

                    # Show button menu using RISK_AREA_BUTTONS format
                    msg = assessment_header + f"✅ **All questions for '{answered_area}' are complete!**\n\n"
                    msg += "RISK_AREA_BUTTONS:" + "|".join(area_names)

                    context['last_message'] = msg
                    context['active_risk_areas'] = area_names
                    context['remaining_risk_area_ids'] = remaining_areas  # Store IDs for easy mapping
                    context['awaiting_risk_area_selection'] = True
                    context['risk_area'] = None  # Clear current risk area to force selection
                    logger.debug(f"Set awaiting_risk_area_selection=True, cleared risk_area")
                else:
                    # Remove extra line breaks that cause formatting issues in frontend
                    context['last_message'] = assessment_header + (
                        f"✅ All questions for '{answered_area}' are complete!\n\n"
                        "🎉 **You have completed all risk areas for this assessment!**\n\n"
                        "**Next Steps:**\n"
                        "• Type 'review my answers' to see all your responses\n"
                        "• Type 'finalize assessment' to submit for review\n\n"
                        "**Note:** Finalizing will change status to Submitted, lock your answers, and generate an assessor review link."
                    )
                    context['awaiting_risk_area_selection'] = False
                return context['last_message']
            next_q = q_result.get("next_question")
            if not next_q:
                context['last_message'] = assessment_header + "No further questions found for this risk area."
                return context['last_message']
            
            # Calculate question progress for this risk area
            from backend.tools.question_tools import get_decision_tree
            decision_tree = get_decision_tree()
            current_risk_area = next_q.get('risk_area', risk_area_id)
            
            # Get all questions for this risk area
            all_questions_for_area = [
                q for q in decision_tree.get('questions', [])
                if q.get('risk_area') == current_risk_area
            ]
            total_questions = len(all_questions_for_area)
            
            # Get current answers for this risk area
            all_answers = assessment.get('answers_by_risk_area', {})
            current_answers = all_answers.get(current_risk_area, {})
            answered_count = len(current_answers)
            current_question_num = answered_count + 1  # The one we're about to answer
            
            # Step 5: Try to get AI answer suggestion
            from backend.tools.answer_suggestion_tool import suggest_answer_from_context
            suggestion = await suggest_answer_from_context(
                assessment_id=assessment_id,
                question_text=next_q["question"],
                question_type=next_q.get("type", "text"),
                options=next_q.get("options", [])
            )
            context['suggestion'] = suggestion
            
            # Compose helpful, context-rich response with progress indicator
            risk_area_name = ra_map.get(current_risk_area, current_risk_area)
            question_level = next_q.get('level', 'L1')  # Get level from question, default to L1

            # Add risk area and level indicators next to TRA number (on same line, no pin icon)
            response = (
                f"<div style='display: flex; align-items: center; gap: 8px; margin-bottom: 12px;'>"
                f"<span style='font-weight: 600; font-size: 1.1rem;'>{assessment_id}</span>"
                f"<button onclick=\"navigator.clipboard.writeText('{assessment_id}').then(() => {{ "
                f"const btn = event.target; const orig = btn.innerHTML; btn.innerHTML = '✓ Copied'; "
                f"setTimeout(() => btn.innerHTML = orig, 2000); }})\" "
                f"style='padding: 4px 8px; background: #e5e7eb; border: 1px solid #d1d5db; border-radius: 4px; "
                f"cursor: pointer; font-size: 0.75rem; color: #374151; transition: all 0.2s;' "
                f"onmouseover=\"this.style.background='#d1d5db'\" "
                f"onmouseout=\"this.style.background='#e5e7eb'\" "
                f"title='Copy TRA ID'>"
                f"<svg style='width: 12px; height: 12px; display: inline; vertical-align: middle;' fill='none' stroke='currentColor' viewBox='0 0 24 24'>"
                f"<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z'></path>"
                f"</svg> Copy"
                f"</button>"
                f"<div style='display: inline-block; padding: 4px 10px; background: #374151; "
                f"border: 1px solid #4b5563; border-radius: 5px;'>"
                f"<span style='font-size: 0.75rem; color: #ffffff; font-weight: 600;'>{risk_area_name}</span>"
                f"</div>"
                f"<div style='display: inline-block; padding: 4px 10px; background: #6b7280; "
                f"border: 1px solid #9ca3af; border-radius: 5px;'>"
                f"<span style='font-size: 0.75rem; color: #ffffff; font-weight: 600;'>{question_level}</span>"
                f"</div>"
                f"</div>\n\n"
            )
            
            # Add AI suggestion BEFORE the question - use simple text format, let frontend handle styling
            if suggestion.get("has_suggestion"):
                response += (
                    f"💡 AI Suggestion: {suggestion['suggested_answer']} (Confidence: {suggestion['confidence'].capitalize()})\n\n"
                )
            else:
                response += "No confident AI suggestion found for this question.\n\n"
            
            # Add the question text
            response += f"{next_q['question']}\n\n"

            # Add options if available
            options = next_q.get("options", [])
            if options:
                response += "Your options are:\n"
                for opt in options:
                    response += f"• {opt.get('label', opt.get('value'))}\n"
                response += "\n"

            response += "You can accept the suggestion, pick an option, or provide your own answer."

            # Add hidden marker for frontend to detect question type (for free-text detection)
            question_type = next_q.get("type", "text")
            response += f"\n[QUESTION_TYPE:{question_type}]"

            context['last_message'] = response
            return response
        except Exception as e:
            logger.debug(f"QuestionAgent error: {e}")
            context['last_error'] = str(e)
            return f"Question Agent error: {str(e)}"
    
    async def stream_async(self, message: str, context: Dict[str, Any] = None) -> AsyncIterator[Dict[str, Any]]:
        """Stream processing with question tools."""
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
            "name": "Question Agent",
            "domain": "Question Flow Management",
            "tools": 2,
            "status": "active"
        }
    
    async def _handle_qualifying_questions(self, message: str, context: Dict[str, Any]) -> str:
        """Handle qualifying questions to automatically determine risk areas."""
        from backend.tools.question_tools import get_decision_tree
        from backend.tools.assessment_tools import get_assessment
        from backend.tools.risk_area_tools import add_risk_area
        
        decision_tree = get_decision_tree()
        qualifying_questions = decision_tree.get('qualifying_questions', [])
        
        # Get assessment
        assessment_id = context.get('assessment_id')
        if not assessment_id:
            context['qualifying_questions_mode'] = False
            return "Error: No assessment ID found. Please create or select an assessment first."
        
        assessment_result = await get_assessment(assessment_id)
        if not assessment_result.get("success"):
            context['qualifying_questions_mode'] = False
            return f"Could not retrieve assessment: {assessment_result.get('error')}"
        
        assessment = assessment_result.get("assessment", {})
        assessment_title = assessment.get('title', 'Untitled')
        
        # Check if message is "start qualifying questions"
        if message.lower() == "start qualifying questions":
            # Initialize qualifying questions flow
            context['current_qualifying_question'] = 'C-01'
            context['qualifying_answers'] = {}
            
            # Find first question
            current_q = next((q for q in qualifying_questions if q['id'] == 'C-01'), None)
            if not current_q:
                context['qualifying_questions_mode'] = False
                return "Error: Could not find qualifying questions in decision tree."
            
            response = f"📋 AI Risk Area Identification for {assessment_title}\n\n"
            response += "I'll ask you a few questions to automatically identify relevant risk areas for your assessment.\n\n"
            response += f"**Question 1 of {len(qualifying_questions)}**\n"
            response += f"{current_q['question']}\n"
            
            if current_q['response_type'] == 'Yes/No':
                response += "\nPlease answer: Yes or No"
            else:
                response += "\nPlease provide your answer:"
            
            context['last_message'] = response
            return response
        
        # Process answer to current question
        current_q_id = context.get('current_qualifying_question')
        if not current_q_id:
            context['qualifying_questions_mode'] = False
            return "Error: Lost track of current question. Please try again."
        
        # Save the answer
        qualifying_answers = context.get('qualifying_answers', {})
        qualifying_answers[current_q_id] = message
        context['qualifying_answers'] = qualifying_answers
        
        # Find current question details
        current_q = next((q for q in qualifying_questions if q['id'] == current_q_id), None)
        # Check if answer contains "yes" (case-insensitive) - more flexible matching
        message_lower = message.lower().strip()
        is_yes_answer = (
            message_lower == 'yes' or 
            message_lower == 'y' or 
            message_lower.startswith('yes ') or 
            message_lower.startswith('yes,') or
            ' yes' in message_lower
        )
        
        if current_q and current_q.get('on_yes') and is_yes_answer:
            # This question triggers a risk area
            risk_area_to_add = current_q['on_yes'].get('risk_area')
            if risk_area_to_add:
                # Map risk area name to ID
                risk_areas_raw = decision_tree.get('risk_areas', {})
                risk_area_id = None
                
                if isinstance(risk_areas_raw, dict):
                    # Find the ID for this risk area name
                    # Create a mapping of trigger names to area IDs
                    # Handle special cases: "Artificial Intelligence" -> "AI Risk", "Intellectual Property" -> "IP Risk"
                    for area_id, area_data in risk_areas_raw.items():
                        area_name = area_data.get('name', '')
                        
                        # Direct matches
                        if area_name == f"{risk_area_to_add} Risk" or area_name == risk_area_to_add:
                            risk_area_id = area_id
                            break
                        
                        # Special case: "Artificial Intelligence" triggers "AI Risk"
                        if risk_area_to_add == "Artificial Intelligence" and area_name == "AI Risk":
                            risk_area_id = area_id
                            break
                        
                        # Special case: "Intellectual Property" triggers "IP Risk"
                        if risk_area_to_add == "Intellectual Property" and area_name == "IP Risk":
                            risk_area_id = area_id
                            break
                        
                        # Fallback: partial match
                        if risk_area_to_add in area_name or area_name.replace(' Risk', '') == risk_area_to_add:
                            risk_area_id = area_id
                            break
                
                if risk_area_id:
                    # Add this risk area to the list to be added later
                    triggered_areas = context.get('triggered_risk_areas', [])
                    if risk_area_id not in triggered_areas:
                        triggered_areas.append(risk_area_id)
                    context['triggered_risk_areas'] = triggered_areas
                    logger.debug(f"Triggered risk area: {risk_area_to_add} -> {risk_area_id}")
                else:
                    logger.debug(f"WARNING: Could not map risk area '{risk_area_to_add}' to an ID")
        
        # Find next question
        current_index = next((i for i, q in enumerate(qualifying_questions) if q['id'] == current_q_id), -1)
        
        if current_index < len(qualifying_questions) - 1:
            # Move to next question
            next_q = qualifying_questions[current_index + 1]
            context['current_qualifying_question'] = next_q['id']
            
            response = f"**Question {current_index + 2} of {len(qualifying_questions)}**\n"
            response += f"{next_q['question']}\n"
            
            if next_q['response_type'] == 'Yes/No':
                response += "\nPlease answer: Yes or No"
            else:
                response += "\nPlease provide your answer:"
            
            context['last_message'] = response
            return response
        else:
            # All questions answered - add triggered risk areas
            triggered_areas = context.get('triggered_risk_areas', [])
            context['qualifying_questions_mode'] = False  # Exit qualifying mode
            
            if triggered_areas:
                # Add all triggered risk areas to assessment
                added_areas = []
                for area_id in triggered_areas:
                    result = await add_risk_area(assessment_id, area_id)
                    if result.get('success'):
                        # Get area name for display
                        risk_areas_raw = decision_tree.get('risk_areas', {})
                        area_name = risk_areas_raw.get(area_id, {}).get('name', area_id)
                        added_areas.append(area_name)
                
                response = "✅ AI Risk Area Identification Complete!\n\n"
                response += f"Based on your answers, I've identified and added the following risk areas to your assessment:\n\n"
                for area in added_areas:
                    response += f"• {area}\n"
                response += "\n"
                response += "**What would you like to do next?**\n\n"
                response += "A) Start answering questions for these risk areas\n"
                response += "B) Add more risk areas manually\n"
                response += "C) View assessment status"
                
                # Clear qualifying questions context
                context.pop('current_qualifying_question', None)
                context.pop('qualifying_answers', None) 
                context.pop('triggered_risk_areas', None)
                
                context['last_message'] = response
                return response
            else:
                response = "✅ AI Risk Area Identification Complete!\n\n"
                response += "Based on your answers, no specific risk areas were triggered for automatic addition.\n\n"
                response += "This might mean:\n"
                response += "• Your project has minimal risk exposure\n"
                response += "• You may want to manually select specific risk areas\n\n"
                response += "**Next Steps:**\n"
                response += "• Type 'select from standard risk areas' to manually choose areas\n"
                response += "• Type 'upload documents' for AI-powered analysis\n"
                response += "• Type 'status' to see your assessment"
                
                # Clear qualifying questions context
                context.pop('current_qualifying_question', None)
                context.pop('qualifying_answers', None)
                context.pop('triggered_risk_areas', None)
                
                context['last_message'] = response
                return response
