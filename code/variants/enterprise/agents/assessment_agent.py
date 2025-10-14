"""
Assessment Agent - Domain Expert for Assessment Lifecycle Management
Handles creating, updating, listing, and managing TRA assessments
"""

from typing import Dict, Any, AsyncIterator

from strands import Agent
from strands.models import BedrockModel
from strands.session import FileSessionManager

from backend.core.config import get_settings
from backend.tools import (
    create_assessment,
    update_assessment,
    list_assessments,
    get_assessment,
    switch_assessment,
)


class AssessmentAgent:
    """
    Specialized agent for assessment lifecycle management.
    
    Domain Expertise:
    - Creating new TRA assessments
    - Updating assessment metadata
    - Listing available assessments
    - Switching between assessments
    - Assessment data management
    
    Tools: 5 assessment-specific tools
    """
    
    def __init__(self, session_id: str, session_manager: FileSessionManager):
        """
        Initialize Assessment Agent.
        
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
        # Import unified tools from assessment_tools
        from backend.tools.assessment_tools import (
            create_assessment,
            update_assessment,
            list_assessments,
            get_assessment,
            switch_assessment,
        )
        # Import risk area management tools
        from backend.tools.risk_area_tools import (
            add_risk_area,
            remove_risk_area,
            set_risk_areas,
            list_standard_risk_areas,
        )
        # Import question tools for listing risk areas
        from backend.tools.question_tools import get_risk_areas
        
        self.agent = Agent(
            model=model,
            system_prompt=self._get_system_prompt(),
            tools=[
                create_assessment,
                update_assessment,
                list_assessments,
                get_assessment,
                switch_assessment,
                add_risk_area,
                remove_risk_area,
                set_risk_areas,
                get_risk_areas,
                list_standard_risk_areas,
            ],
            callback_handler=None
        )
    
    def _get_system_prompt(self) -> str:
        """Get agent system prompt."""
        return f"""You are the Assessment Management Specialist for the TRA system.

Your expertise: Creating, updating, and managing technology risk assessments.

**Your Responsibilities:**
- Guide users through assessment creation
- Manage assessment metadata and risk areas
- Help users find and switch between assessments
- Ensure proper assessment lifecycle management

**Key Principles:**
- ALWAYS ask for required information before creating assessments
- NEVER make up project names or details
- Provide clear Assessment IDs after creation
- Help users organize multiple assessments

**Risk Area Management:**
- When users ask to "select from standard risk areas" or "see available options", use the list_standard_risk_areas tool
- When users select a risk area, use add_risk_area tool with the assessment_id and risk_area_id
- You can add multiple risk areas to an assessment
- Use get_risk_areas to see which risk areas are currently attached to an assessment

**After Creating Assessment:**
Immediately offer 3 risk identification options in this order:
A) Upload documents for AI-powered risk area recommendation
B) Select from standard risk areas
C) Answer AI questions to identify areas

**When User Asks for Available Risk Areas:**
Use the list_standard_risk_areas tool to show them all available risk areas with descriptions.

**After Adding a Risk Area:**
Do NOT offer the three options again. Instead, confirm the risk area was added and ask if the user wants to start answering questions for that risk area, add another, or finish risk area selection.

Session ID: {self.session_id}
"""
    
    async def invoke_async(self, message: str, context: Dict[str, Any] = None) -> str:
        """Process message with assessment tools and update shared context. Enforce required metadata collection."""
        print(f"[AGENT DEBUG] AssessmentAgent.invoke_async called with message: {message!r}, context: {context!r}")
        if context is None:
            context = {}
        
        # Handle risk area listing requests directly
        import re
        message_lower = message.lower().strip()
        if re.search(r'\b(select|show|list|display|see|view)\b.*(from|available|standard).*risk\s*area', message_lower) or \
           message_lower in ['a', 'option a', 'b', 'option b'] and 'standard risk' in context.get('last_message', '').lower():
            # User wants to see standard risk areas
            from backend.tools.risk_area_tools import list_standard_risk_areas
            result = list_standard_risk_areas()
            
            if result.get('success'):
                risk_areas = result.get('risk_areas', [])
                assessment_id = context.get('assessment_id', '')
                
                msg = [f"Here are the available standard risk areas:\n"]
                for idx, ra in enumerate(risk_areas, 1):
                    msg.append(f"{idx}. {ra.get('icon', '')} {ra.get('name')} - {ra.get('description', '')}")
                
                msg.append(f"\nWhich risk area(s) would you like to add to assessment {assessment_id}?")
                msg.append("You can say the name (e.g., 'Data Security') or number (e.g., '1'), and you can select multiple areas.")
                
                context['last_message'] = "\n".join(msg)
                context['available_risk_areas'] = risk_areas
                return context['last_message']
            else:
                return f"Error listing risk areas: {result.get('error', 'Unknown error')}"
        
        # Handle risk area selection by name or number
        if context.get('available_risk_areas'):
            available_risk_areas = context['available_risk_areas']
            assessment_id = context.get('assessment_id', '')
            
            # Try to match by number (e.g., "1", "2", "1 and 3")
            numbers = re.findall(r'\b(\d+)\b', message_lower)
            selected_areas = []
            
            if numbers:
                for num_str in numbers:
                    idx = int(num_str) - 1
                    if 0 <= idx < len(available_risk_areas):
                        selected_areas.append(available_risk_areas[idx])
            else:
                # Try to match by name (case-insensitive, check if risk area name appears in message)
                for ra in available_risk_areas:
                    ra_name_lower = ra['name'].lower()
                    # Check if the full risk area name or significant parts appear in the message
                    # Split risk area name into words and check if they appear consecutively or nearby
                    name_words = ra_name_lower.split()
                    
                    # Simple check: if all words from the risk area name appear in the message
                    if all(word in message_lower for word in name_words):
                        selected_areas.append(ra)
            
            if selected_areas:
                # Add the selected risk areas
                from backend.tools.risk_area_tools import add_risk_area
                from backend.tools.assessment_tools import get_assessment
                added = []
                print(f"[AGENT DEBUG] Selected risk areas to add: {[ra['name'] for ra in selected_areas]}")
                print(f"[AGENT DEBUG] Assessment ID: {assessment_id}")
                for ra in selected_areas:
                    print(f"[AGENT DEBUG] Adding risk area: {ra['name']} (ID: {ra['id']}) to assessment {assessment_id}")
                    try:
                        result = await add_risk_area(assessment_id, ra['id'])
                        print(f"[AGENT DEBUG] Add risk area result: {result}")
                        if result.get('success'):
                            added.append(ra['name'])
                        else:
                            print(f"[AGENT DEBUG] Add risk area FAILED for {ra['name']}: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        print(f"[AGENT DEBUG] Exception adding risk area {ra['name']}: {e}")
                        import traceback
                        traceback.print_exc()
                
                if added:
                    # Fetch the updated assessment to get latest risk areas
                    print(f"[AGENT DEBUG] Fetching updated assessment after adding {len(added)} risk areas")
                    assessment_result = await get_assessment(assessment_id, context)
                    if assessment_result.get('success') and 'assessment' in assessment_result:
                        context['assessment'] = assessment_result['assessment']
                        print(f"[AGENT DEBUG] Updated assessment in context with active_risk_areas: {assessment_result['assessment'].get('active_risk_areas')}")
                    
                    context['available_risk_areas'] = None  # Clear the selection state
                    msg = f"✅ Successfully added risk area(s): {', '.join(added)} to assessment {assessment_id}.\n\n"
                    msg += "Would you like to:\n"
                    msg += "1. Start answering questions for these risk areas\n"
                    msg += "2. Add more risk areas\n"
                    msg += "3. View current assessment status"
                    context['last_message'] = msg
                    print(f"[AGENT DEBUG] Returning success message for risk area addition")
                    return msg
                else:
                    # Risk areas were selected but failed to add
                    # Keep available_risk_areas in context so user can retry
                    print(f"[AGENT DEBUG] Risk areas were selected but none were successfully added")
                    print(f"[AGENT DEBUG] Selected areas were: {[ra['name'] for ra in selected_areas]}")
                    print(f"[AGENT DEBUG] Assessment ID used: {assessment_id}")
                    # Don't clear available_risk_areas - keep it so retry stays with Assessment Agent
                    error_msg = f"❌ Failed to add the selected risk areas to assessment {assessment_id}.\n\n"
                    error_msg += f"Selected areas: {', '.join([ra['name'] for ra in selected_areas])}\n\n"
                    error_msg += "This might be a database connection issue. Please check the logs for details, or try:\n"
                    error_msg += "- Selecting areas by number instead (e.g., '1 and 3')\n"
                    error_msg += "- Selecting one area at a time"
                    return error_msg
            else:
                # No matches found, clear state and ask for clarification
                print(f"[AGENT DEBUG] No risk areas matched from message: '{message}'")
                context['available_risk_areas'] = None
                return (
                    f"I couldn't identify which risk area(s) you want to add from your message: '{message}'\n\n"
                    "Please select from standard risk areas again and specify either:\n"
                    "- A number (e.g., '1' or '1 and 3')\n"
                    "- A complete risk area name (e.g., 'Data Security')"
                )
        
        # Extract project name from message if provided (robust parsing)
        if not context.get('project_name'):
            # Normalize input
            msg = (message or "").strip()
            extracted = None

            # 1) Explicit patterns e.g. "project name is X", "Project: X", "it's called X"
            patterns = [
                r'(?:project\s*name|name\s*of\s*the\s*project)\s*(?:is|:)\s*["“”\'`]?(.+?)["“”\'`]?$',
                r'(?:project)\s*(?:is|=)\s*["“”\'`]?(.+?)["“”\'`]?$',
                r'^(?:the\s*project\s*name\s*is|it(?:\'|’)s\s*called|called|named)\s+["“”\'`]?(.+?)["“”\'`]?$',
                r'^(?:project\s*name)\s*-\s*["“”\'`]?(.+?)["“”\'`]?$',
                r'^(?:project\s*name)\s*:\s*["“”\'`]?(.+?)["“”\'`]?$',  # "Project Name: XXX"
            ]
            for pat in patterns:
                m = re.search(pat, msg, re.IGNORECASE)
                if m:
                    extracted = m.group(1).strip()
                    break

            # 2) If still not found and we are explicitly waiting for the project name,
            #    treat the whole message as the name (with guards against generic responses)
            if not extracted and context.get('waiting_for_project_name'):
                if not re.search(r'\b(yes|no|option\s*[abc]|start|create|new|next|skip)\b', msg, re.IGNORECASE):
                    # Remove wrapping quotes
                    extracted = re.sub(r'^[\'"“”`]+|[\'"“”`]+$', '', msg).strip()

            # Final cleanup: collapse internal whitespace and trim trailing punctuation
            if extracted:
                extracted = re.sub(r'\s+', ' ', extracted).strip(' .,:;')
                context['project_name'] = extracted
                print(f"[AGENT DEBUG] Extracted project_name (smart): {context['project_name']}")
        
        # Enforce required metadata collection before creation
        # Only Project Name is mandatory; System ID, Classification, and Business Unit are optional
        required_fields = [
            ("project_name", "Project Name"),
        ]
        
        # Determine if user is trying to create an assessment
        create_intent = False
        if isinstance(message, str) and re.search(r"create|new|start", message, re.IGNORECASE):
            create_intent = True
        
        # Also set create_intent if we were previously waiting for project_name and now have it
        if context.get('waiting_for_project_name') and context.get('project_name'):
            create_intent = True
            context['waiting_for_project_name'] = False
        
        # If user is trying to create an assessment, check for missing fields
        if create_intent:
            missing = []
            for key, label in required_fields:
                if not context.get(key):
                    missing.append(label)
            if missing:
                context['missing_fields'] = missing
                context['waiting_for_project_name'] = True
                context['last_message'] = (
                    "To create a new assessment, please provide the following required information:\n" +
                    "\n".join(f"- {field}" for field in missing)
                )
                return context['last_message']
            
            # All required fields present - create the assessment directly
            print(f"[AGENT DEBUG] All required fields present, creating assessment with project_name: {context['project_name']}")
            result = await create_assessment(
                project_name=context['project_name'],
                system_id=context.get('system_id', ''),
                classification=context.get('classification', ''),
                business_unit=context.get('business_unit', 'Default'),
                description=context.get('description', ''),
                session_id=self.session_id,
                context=context
            )
            
            # Format the response
            if result.get('success'):
                assessment_id = result['assessment_id']
                project_name = result['project_name']
                context['assessment_id'] = assessment_id
                
                confirmation_msg = (
                    f"✅ Assessment Created Successfully!\n\n"
                    f"📋 TRA Number: {assessment_id}\n"
                    f"📁 Project Name: {project_name}\n"
                )
                
                if result.get('system_id'):
                    confirmation_msg += f"🔢 System ID: {result['system_id']}\n"
                if result.get('classification'):
                    confirmation_msg += f"🔒 Classification: {result['classification']}\n"
                if result.get('business_unit'):
                    confirmation_msg += f"🏢 Business Unit: {result['business_unit']}\n"
                
                confirmation_msg += (
                    f"\nNow, let's discuss the next steps for this assessment:\n\n"
                    f"A) Upload documents for AI-powered risk area recommendation\n"
                    f"B) Select from standard risk areas\n"
                    f"C) Answer AI questions to identify areas\n\n"
                    f"Which of these options would you like to explore first?"
                )
                
                context['last_message'] = confirmation_msg
                # Clear the project_name from context to allow creating new assessments
                context['project_name'] = None
                return confirmation_msg
            else:
                error_msg = f"Failed to create assessment: {result.get('error', 'Unknown error')}"
                context['last_error'] = error_msg
                return error_msg
        try:
            result = await self.agent.invoke_async(
                message,
                session_manager=self.session_manager
            )
            import re
            # Unified handling for assessment list/get/create/switch
            if isinstance(result, dict):
                # If a new assessment was created, format confirmation message
                if result.get('success') and result.get('assessment_id') and result.get('project_name'):
                    assessment_id = result['assessment_id']
                    project_name = result['project_name']
                    context['assessment_id'] = assessment_id
                    
                    # Format clear confirmation message
                    confirmation_msg = (
                        f"✅ Assessment Created Successfully!\n\n"
                        f"📋 TRA Number: {assessment_id}\n"
                        f"📁 Project Name: {project_name}\n"
                    )
                    
                    if result.get('system_id'):
                        confirmation_msg += f"🔢 System ID: {result['system_id']}\n"
                    if result.get('classification'):
                        confirmation_msg += f"🔒 Classification: {result['classification']}\n"
                    if result.get('business_unit'):
                        confirmation_msg += f"🏢 Business Unit: {result['business_unit']}\n"
                    
                    confirmation_msg += (
                        f"\nNow, let's discuss the next steps for this assessment:\n\n"
                        f"A) Upload documents for AI-powered risk area recommendation\n"
                        f"B) Select from standard risk areas\n"
                        f"C) Answer AI questions to identify areas\n\n"
                        f"Which of these options would you like to explore first?"
                    )
                    
                    context['last_message'] = confirmation_msg
                    return confirmation_msg
                # If assessment_id is returned but no project_name, update context
                elif result.get('success') and result.get('assessment_id'):
                    context['assessment_id'] = result['assessment_id']
                # If an assessment is returned (get/switch), update context['assessment_id']
                if 'assessment' in result:
                    a = result['assessment']
                    context['assessment'] = a
                    if a.get('assessment_id'):
                        context['assessment_id'] = a['assessment_id']
                    # --- CONTEXT-AWARE NEXT-STEP LOGIC ---
                    assessment_id = a.get('assessment_id', 'Unknown')
                    assessment_title = a.get('title', 'Untitled')
                    assessment_state = a.get('current_state', '')
                    assessment_created = a.get('created_at', '')
                    assessment_completion = a.get('completion_percentage', 0)
                    assessment_desc = a.get('description', '')
                    assessment_header = f"Assessment: {assessment_title} (ID: {assessment_id})\nState: {assessment_state}\nCreated: {assessment_created}\nCompletion: {assessment_completion}%\nDescription: {assessment_desc}\n"
                    # Risk area logic
                    active_risk_areas = a.get('active_risk_areas', [])
                    from backend.tools.question_tools import get_decision_tree
                    decision_tree = get_decision_tree()
                    # Handle both dict format (decision_tree2.yaml) and list format
                    risk_areas_raw = decision_tree.get('risk_areas', {})
                    if isinstance(risk_areas_raw, dict):
                        # decision_tree2.yaml format: dict with keys like 'third_party'
                        ra_map = {area_id: area_data.get('name', area_id) for area_id, area_data in risk_areas_raw.items()}
                    else:
                        # decision_tree.yaml format: list of dicts
                        ra_map = {ra['id']: ra['name'] for ra in risk_areas_raw}
                    if not active_risk_areas:
                        context['last_message'] = assessment_header + (
                            "No risk areas are currently attached to this assessment. "
                            "You can add a risk area by saying 'add risk area' or 'select from standard risk areas'."
                        )
                        return context['last_message']
                    elif len(active_risk_areas) == 1:
                        ra_name = ra_map.get(active_risk_areas[0], active_risk_areas[0])
                        context['last_message'] = assessment_header + (
                            f"This assessment has one risk area attached: {ra_name}.\n"
                            "Would you like to start answering questions for this risk area now? (yes/no) "
                            "Or you can add more risk areas."
                        )
                        return context['last_message']
                    else:
                        area_names = [ra_map.get(r, r) for r in active_risk_areas]
                        # Format as buttons for frontend
                        context['last_message'] = assessment_header + (
                            "Multiple risk areas are attached to this assessment. "
                            "Please select which area you want to answer questions for:\n\n"
                            "RISK_AREA_BUTTONS:" + "|".join(area_names)
                        )
                        return context['last_message']
                if 'assessments' in result:
                    assessments = result['assessments']
                    context['assessments'] = assessments
                    if not assessments:
                        context['last_message'] = (
                            "There are currently no assessments in the system. "
                            "You can create a new assessment by providing the project name, system/project ID, data classification, business unit, and an optional description. "
                            "Once created, it will appear in the global assessment list."
                        )
                        return context['last_message']
                    else:
                        msg = ["Here is the global list of all assessments:"]
                        for idx, a in enumerate(assessments, 1):
                            msg.append(f"{idx}. {a.get('title', 'Untitled')} (ID: {a.get('assessment_id', 'N/A')}, State: {a.get('current_state', '')}, Created: {a.get('created_at', '')}, Completion: {a.get('completion_percentage', 0)}%)")
                        context['last_message'] = "\n".join(msg)
                        return context['last_message']
                if 'success' in result and result.get('success') is False:
                    context['last_error'] = result.get('error', 'Unknown error')
                    return f"Assessment Agent error: {context['last_error']}"
            # Fallback: try to extract assessment_id from message string if present
            msg_str = str(result)
            match = re.search(r"Assessment ID[:= ]+([A-Z0-9\-]+)", msg_str)
            if match:
                context['assessment_id'] = match.group(1)
            context['last_message'] = msg_str
            return context['last_message']
        except Exception as e:
            print(f"[AGENT DEBUG] AssessmentAgent error: {e}")
            context['last_error'] = str(e)
            return f"Assessment Agent error: {str(e)}"
    
    async def stream_async(self, message: str, context: Dict[str, Any] = None) -> AsyncIterator[Dict[str, Any]]:
        """Stream processing with assessment tools."""
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
            "name": "Assessment Agent",
            "domain": "Assessment Lifecycle",
            "tools": 5,
            "status": "active"
        }
