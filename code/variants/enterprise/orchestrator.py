"""
Enterprise Orchestrator Agent
Routes requests to specialized domain agents using Strands 1.x patterns
"""


from typing import Dict, Any, AsyncIterator
from datetime import datetime
import re

from strands import Agent
from strands.models import BedrockModel
from strands.session import FileSessionManager

from backend.core.config import get_settings
from .agents.assessment_agent import AssessmentAgent
from .agents.document_agent import DocumentAgent
from .agents.question_agent import QuestionAgent
from .agents.status_agent import StatusAgent


class EnterpriseOrchestratorAgent:
    """
    Enterprise TRA Orchestrator - Multi-Agent Architecture
    
    Routes user requests to specialized domain agents:
    - Assessment Agent: Lifecycle management
    - Document Agent: RAG & analysis
    - Question Agent: Questionnaire flow
    - Status Agent: Reporting & export
    
    Features:
    - Intelligent routing based on user intent
    - Shared state management across agents
    - Strands 1.x native implementation
    - Production-ready error handling
    """
    
    def __init__(self, session_id: str = None):
        """
        Initialize Enterprise Orchestrator with specialized agents.
        
        Args:
            session_id: Session identifier for state management
        """
        self.settings = get_settings()
        self.session_id = session_id or f"enterprise_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{id(self)}"
        
        # Initialize Strands session manager (shared across agents)
        self.session_manager = FileSessionManager(
            session_id=self.session_id,
            storage_dir=self.settings.session_storage_dir
        )
        
        # Initialize specialized agents
        self.assessment_agent = AssessmentAgent(self.session_id, self.session_manager)
        self.document_agent = DocumentAgent(self.session_id, self.session_manager)
        self.question_agent = QuestionAgent(self.session_id, self.session_manager)
        self.status_agent = StatusAgent(self.session_id, self.session_manager)
        
        # Initialize Bedrock model for orchestrator
        model = BedrockModel(
            model_id=self.settings.bedrock_model_id,
            temperature=0.7,
            streaming=True
        )
        
        # Create orchestrator agent (meta-agent that routes)
        self.orchestrator = Agent(
            model=model,
            system_prompt=self._get_orchestrator_prompt(),
            tools=[],  # Orchestrator doesn't have tools, delegates to specialists
            callback_handler=None
        )
        
        # Routing patterns
        self.routing_patterns = {
            'assessment': [
                r'\b(create|new|start)\s+(assessment|tra)\b',
                r'\b(update|modify|change)\s+(assessment|tra)\b',
                r'\b(get|retrieve|load)\s+assessment\b',
                r'\b(switch|change)\s+to\s+assessment\b',
            ],
            'document': [
                r'\b(upload|add|attach)\s+(document|file|doc)\b',
                r'\b(analyze|review|examine)\s+(document|file)\b',
                r'\b(search|find|look\s+for)\s+.*(document|knowledge\s+base)\b',
                r'\b(suggest|recommend)\s+risk\s+areas?\b',
                r'\bwhat.*document\b',
            ],
            'question': [
                r'\b(continue|resume|start)\s+(questions?|assessment)\b',
                r'\b(answer|respond\s+to)\s+question\b',
                r'\b(next|get)\s+question\b',
                r'\bquestion\s+flow\b',
                r'^(continue|next)\s+TRA-\d{4}-[A-Z0-9]+',
            ],
            'status': [
                r'\b(status|state|progress)\b',
                r'\b(export|download|generate)\s+report\b',
                r'\b(assessor|reviewer)\s+link\b',
                r'\b(summary|overview)\s+of\s+assessment\b',
                r'\bhow\s+(far|much).*complete\b',
                r'\b(list|show|display|enumerate|get\s+all)\s+(assessments?|documents?|files?|knowledge\s*base|kb\s*items?)\b',
                r'\b(review|show|display)\s+(answers?|responses?)\b',
                r'\b(finali[sz]e|submit|complete)\s+(assessment|tra)\b',
            ],
        }
    
    def _get_orchestrator_prompt(self) -> str:
        """Get orchestrator system prompt."""
        return """You are the Enterprise TRA Orchestrator coordinating specialized agents.

Your role is to understand user intent and route to the appropriate specialist:

**Assessment Agent** - For creating, updating, listing, and managing TRA assessments
**Document Agent** - For uploading, analyzing documents, and suggesting answers from context  
**Question Agent** - For answering TRA questions and managing question flow
**Status Agent** - For checking progress, generating reports, and exporting data

You analyze user requests and delegate to the right specialist, then synthesize their responses.

Session ID: {session_id}
""".format(session_id=self.session_id)
    
    async def _determine_agent(self, message: str, context: Dict[str, Any] = None):
        """
        Strands-agents-compliant intent extraction:
        - Use SLM (LLM) to extract intent, confidence, and reasoning.
        - If SLM is ambiguous or low confidence, prompt user for clarification.
        - Fallback to regex/keyword if SLM fails.
        - Log all steps in context.
        - Return: agent, updated context, and (if needed) a clarification prompt.
        """
        if context is None:
            context = {}
        print(f"[ORCH DEBUG] _determine_agent called with message: {message!r}")
        
        # Check if this is a follow-up response (yes/no, short answer, etc.)
        message_lower = message.lower().strip()
        
        # PRIORITY CHECKS - Must be at the very top before any other routing logic
        
        # Priority 0: If we're in qualifying questions mode, ALWAYS route to Question Agent
        if context.get('qualifying_questions_mode'):
            agent_type = 'question'
            context['intent_extraction'] = {
                'method': 'qualifying_questions_mode',
                'intent': [agent_type],
                'confidence': 1.0,
                'reasoning': 'In qualifying questions mode, routing to Question Agent'
            }
            context['clarification_needed'] = False
            context['clarification_prompt'] = None
            context['last_routed_agent'] = agent_type
            print(f"[ORCH DEBUG] Qualifying questions mode active, routing to: {agent_type}")
            return self.question_agent, context, None
        
        # Priority 1: Finalize/submit commands should always go to Status Agent
        finalize_pattern = r'\b(finali[sz]e|submit)(\s+(assessment|tra))?\b'
        if re.search(finalize_pattern, message_lower, re.IGNORECASE):
            agent_type = 'status'
            context['intent_extraction'] = {
                'method': 'priority_finalize',
                'intent': [agent_type],
                'confidence': 1.0,
                'reasoning': 'Finalize/submit command detected, routing to Status Agent'
            }
            context['clarification_needed'] = False
            context['clarification_prompt'] = None
            context['last_routed_agent'] = agent_type
            print(f"[ORCH DEBUG] Priority finalize detected, routing to: {agent_type}")
            return self.status_agent, context, None
        
        # Priority 2: Review answers commands should always go to Status Agent
        review_pattern = r'\b(review|show|display)\s+(my\s+)?(answers?|responses?)\b'
        if re.search(review_pattern, message_lower, re.IGNORECASE):
            agent_type = 'status'
            context['intent_extraction'] = {
                'method': 'priority_review',
                'intent': [agent_type],
                'confidence': 1.0,
                'reasoning': 'Review answers command detected, routing to Status Agent'
            }
            context['clarification_needed'] = False
            context['clarification_prompt'] = None
            context['last_routed_agent'] = agent_type
            print(f"[ORCH DEBUG] Priority review detected, routing to: {agent_type}")
            return self.status_agent, context, None
        
        # PRIORITY: Check if we're awaiting risk area selection after completing a risk area
        if context.get('awaiting_risk_area_selection'):
            # User is selecting the next risk area to continue
            # Check if message is a number (1, 2, etc.) or a risk area name
            remaining_ids = context.get('remaining_risk_area_ids', [])
            
            # Try to match by number
            if message_lower.isdigit():
                idx = int(message_lower) - 1
                if 0 <= idx < len(remaining_ids):
                    # Valid selection, route to Question Agent
                    agent_type = 'question'
                    context['intent_extraction'] = {
                        'method': 'risk_area_number_selection',
                        'intent': [agent_type],
                        'confidence': 1.0,
                        'reasoning': f'User selected risk area #{message_lower} from completion menu'
                    }
                    context['clarification_needed'] = False
                    context['clarification_prompt'] = None
                    context['last_routed_agent'] = agent_type
                    # Clear the awaiting flag
                    context['awaiting_risk_area_selection'] = False
                    print(f"[ORCH DEBUG] Risk area number selection detected: {message_lower}, routing to Question Agent")
                    return self.question_agent, context, None
            
            # Try to match by name
            from backend.tools.question_tools import get_decision_tree
            decision_tree = get_decision_tree()
            # Handle both dict format (decision_tree2.yaml) and list format
            risk_areas_raw = decision_tree.get('risk_areas', {})
            if isinstance(risk_areas_raw, dict):
                # decision_tree2.yaml format: dict with keys like 'third_party'
                ra_map = {area_id: area_data.get('name', area_id).lower() for area_id, area_data in risk_areas_raw.items()}
            else:
                # decision_tree.yaml format: list of dicts
                ra_map = {ra['id']: ra['name'].lower() for ra in risk_areas_raw}
            
            for ra_id in remaining_ids:
                ra_name = ra_map.get(ra_id, '').lower()
                if ra_name in message_lower or message_lower in ra_name:
                    # Valid selection, route to Question Agent
                    agent_type = 'question'
                    context['intent_extraction'] = {
                        'method': 'risk_area_name_selection',
                        'intent': [agent_type],
                        'confidence': 1.0,
                        'reasoning': f'User selected risk area "{message}" from completion menu'
                    }
                    context['clarification_needed'] = False
                    context['clarification_prompt'] = None
                    context['last_routed_agent'] = agent_type
                    # Clear the awaiting flag
                    context['awaiting_risk_area_selection'] = False
                    print(f"[ORCH DEBUG] Risk area name selection detected: {message}, routing to Question Agent")
                    return self.question_agent, context, None
        
        # IMPORTANT: Check if we're in the middle of a question flow BEFORE checking for risk area names
        # If there's a current_question_id or we just presented a question, this is an ANSWER, not a risk area selection
        from backend.tools.assessment_tools import get_assessment
        if context.get('assessment_id'):
            assessment_result = await get_assessment(context['assessment_id'])
            if assessment_result.get('success'):
                assessment = assessment_result.get('assessment', {})
                current_question_id = assessment.get('current_question_id')
                
                # If there's a current question, user is answering it - route to Question Agent
                if current_question_id:
                    agent_type = 'question'
                    context['intent_extraction'] = {
                        'method': 'answering_current_question',
                        'intent': [agent_type],
                        'confidence': 1.0,
                        'reasoning': 'User is answering current question (current_question_id present)'
                    }
                    context['clarification_needed'] = False
                    context['clarification_prompt'] = None
                    context['last_routed_agent'] = agent_type
                    print(f"[ORCH DEBUG] User is answering current question, routing to: {agent_type}")
                    return self.question_agent, context, None
        
        # Special case: Check if message is a risk area name/selection (when in question flow context)
        # BUT ONLY if we're NOT already in the middle of answering questions or selecting risk areas for the assessment
        # If context['available_risk_areas'] is set, the Assessment Agent should handle it
        if not context.get('available_risk_areas'):
            from backend.tools.question_tools import get_decision_tree
            decision_tree = get_decision_tree()
            # Handle both dict format (decision_tree2.yaml) and list format
            risk_areas_raw = decision_tree.get('risk_areas', {})
            if isinstance(risk_areas_raw, dict):
                # decision_tree2.yaml format: dict with keys like 'third_party'
                risk_area_names = [area_data.get('name', area_id).lower() for area_id, area_data in risk_areas_raw.items()]
                risk_area_ids = [area_id.lower() for area_id in risk_areas_raw.keys()]
            else:
                # decision_tree.yaml format: list of dicts
                risk_area_names = [ra['name'].lower() for ra in risk_areas_raw]
                risk_area_ids = [ra['id'].lower() for ra in risk_areas_raw]
            
            # Check if message matches a risk area (by name or partial match)
            is_risk_area_selection = False
            for ra_name in risk_area_names:
                if ra_name in message_lower or message_lower in ra_name:
                    is_risk_area_selection = True
                    break
            if not is_risk_area_selection:
                for ra_id in risk_area_ids:
                    if ra_id in message_lower or message_lower in ra_id:
                        is_risk_area_selection = True
                        break
            
            # If this is a risk area selection, route to Question Agent
            if is_risk_area_selection:
                agent_type = 'question'
                context['intent_extraction'] = {
                    'method': 'risk_area_selection',
                    'intent': [agent_type],
                    'confidence': 0.95,
                    'reasoning': 'Message matches a risk area name, routing to Question Agent'
                }
                context['clarification_needed'] = False
                context['clarification_prompt'] = None
                context['last_routed_agent'] = agent_type
                print(f"[ORCH DEBUG] Detected risk area selection, routing to: {agent_type}")
                return self.question_agent, context, None
        
        # Check if we're in a context where we're waiting for specific information
        waiting_for_info = any([
            context.get('waiting_for_project_name'),
            context.get('missing_fields'),
            context.get('available_risk_areas')
        ])
        
        is_follow_up = any([
            message_lower in ['yes', 'no', 'ok', 'okay', 'sure', 'please', 'continue', 'proceed'],
            message_lower.startswith('yes '),
            message_lower.startswith('no '),
            message_lower.startswith('please ') and 'question' not in message_lower,  # Don't treat "please start questions" as follow-up
            message_lower.startswith('i am ready'),
            message_lower.startswith("i'm ready"),
            message_lower.startswith('ready to'),
            message_lower.startswith("let's"),
            message_lower.startswith('lets'),
            re.search(r'\b(ready|proceed|continue|move)\b.*(next|forward|ahead)', message_lower) and context.get('last_routed_agent'),
            len(message.split()) <= 5 and context.get('last_routed_agent'),  # Short responses with previous agent context
            waiting_for_info  # We're waiting for specific information from user
        ])
        
        # Special case: If message contains "start" or "begin" AND "question", route to Question Agent
        if re.search(r'\b(start|begin|answer)\b.*\bquestion', message_lower) or re.search(r'\bquestion.*\b(start|begin)', message_lower):
            agent_type = 'question'
            context['intent_extraction'] = {
                'method': 'question_intent',
                'intent': [agent_type],
                'confidence': 0.95,
                'reasoning': 'Message explicitly requests to start/begin questions'
            }
            context['clarification_needed'] = False
            context['clarification_prompt'] = None
            context['last_routed_agent'] = agent_type
            print(f"[ORCH DEBUG] Detected question start intent, routing to: {agent_type}")
            return self.question_agent, context, None
        
        # If this looks like a follow-up and we have a last agent, route to same agent
        if is_follow_up and context.get('last_routed_agent'):
            last_agent_type = context['last_routed_agent']
            agent = self._get_agent_by_type(last_agent_type)
            print(f"[ORCH DEBUG] Detected follow-up message, routing to previous agent: {last_agent_type}")
            context['intent_extraction'] = {
                'method': 'follow_up',
                'intent': [last_agent_type],
                'confidence': 0.9,
                'reasoning': f"Follow-up response detected, continuing with {last_agent_type} agent"
            }
            return agent, context, None
        
        reasoning = ""
        intent = None
        confidence = 0.0
        clarification_prompt = None
        
        # PRIORITY CHECK: Finalize/submit commands should always go to Status Agent
        # Match "finalize assessment", "submit tra", or just "finalize"/"submit"
        finalize_pattern = r'\b(finali[sz]e|submit)(\s+(assessment|tra))?\b'
        if re.search(finalize_pattern, message_lower, re.IGNORECASE):
            agent_type = 'status'
            context['intent_extraction'] = {
                'method': 'priority_finalize',
                'intent': [agent_type],
                'confidence': 1.0,
                'reasoning': 'Finalize/submit command detected, routing to Status Agent'
            }
            context['clarification_needed'] = False
            context['clarification_prompt'] = None
            context['last_routed_agent'] = agent_type
            print(f"[ORCH DEBUG] Priority finalize detected, routing to: {agent_type}")
            return self.status_agent, context, None
        
        # Step 1: SLM intent extraction with confidence
        try:
            prompt = (
                "Classify the user request into one or more of these agent types: assessment, document, question, status. "
                "Respond in JSON: {intent: [agent_types], confidence: float (0-1), reasoning: string}. "
                "If ambiguous, set confidence < 0.7 and explain in reasoning.\n\n"
                "User message: '" + message + "'"
            )
            intent_response = await self.orchestrator.invoke_async(prompt)
            # Try to parse JSON response
            import json
            try:
                parsed = json.loads(intent_response.text if hasattr(intent_response, 'text') else str(intent_response))
                intent = parsed.get('intent')
                confidence = float(parsed.get('confidence', 0.0))
                reasoning = parsed.get('reasoning', '')
            except Exception as e:
                # Fallback: treat as plain text
                intent_text = intent_response.text if hasattr(intent_response, 'text') else str(intent_response)
                intent = [intent_text.strip().lower()]
                confidence = 0.5
                reasoning = f"SLM returned non-JSON, fallback to text: {intent_text.strip()}"
            print(f"[ORCH DEBUG] SLM intent extraction result: {intent!r}, confidence: {confidence}, reasoning: {reasoning}")
            context['intent_extraction'] = {
                'method': 'slm',
                'intent': intent,
                'confidence': confidence,
                'reasoning': reasoning,
                'raw_response': intent_response.text if hasattr(intent_response, 'text') else str(intent_response)
            }
            # If ambiguous or low confidence, prompt user for clarification
            if not intent or confidence < 0.7:
                clarification_prompt = (
                    "I'm not sure what you want to do. "
                    "Could you clarify if your request is about an assessment, document, question, or status? "
                    f"Reasoning: {reasoning}"
                )
                context['clarification_needed'] = True
                context['clarification_prompt'] = clarification_prompt
                print(f"[ORCH DEBUG] Clarification needed: {clarification_prompt}")
                return None, context, clarification_prompt
            # If multi-intent, prefer to prompt for clarification
            if isinstance(intent, list) and len(intent) > 1:
                clarification_prompt = (
                    f"Your request could relate to multiple areas: {', '.join(intent)}. "
                    "Please specify which you want to proceed with."
                )
                context['clarification_needed'] = True
                context['clarification_prompt'] = clarification_prompt
                print(f"[ORCH DEBUG] Multi-intent clarification needed: {clarification_prompt}")
                return None, context, clarification_prompt
            # Single intent, high confidence
            agent_type = intent[0] if isinstance(intent, list) else intent
            agent = self._get_agent_by_type(agent_type)
            context['clarification_needed'] = False
            context['clarification_prompt'] = None
            context['last_routed_agent'] = agent_type
            print(f"[ORCH DEBUG] Routing to agent (SLM): {agent_type}")
            return agent, context, None
        except Exception as e:
            reasoning += f"SLM intent extraction failed: {e}\n"
            print(f"[ORCH DEBUG] SLM intent extraction failed: {e}")
            context['intent_extraction'] = {
                'method': 'slm',
                'intent': None,
                'confidence': 0.0,
                'reasoning': reasoning,
                'raw_response': None
            }
        # Step 2: Fallback to regex/keyword
        message_lower = message.lower()
        for agent_type, patterns in self.routing_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    reasoning += f"Regex matched pattern '{pattern}' for agent '{agent_type}'. "
                    context['intent_extraction'] = {
                        'method': 'regex',
                        'intent': [agent_type],
                        'confidence': 0.8,
                        'reasoning': reasoning,
                        'raw_response': None
                    }
                    context['clarification_needed'] = False
                    context['clarification_prompt'] = None
                    context['last_routed_agent'] = agent_type
                    print(f"[ORCH DEBUG] Routing to agent (regex): {agent_type}")
                    return self._get_agent_by_type(agent_type), context, None
        # Step 3: Fallback to keywords
        if any(word in message_lower for word in ['create', 'new', 'start', 'list']):
            agent_type = 'assessment'
            reasoning += "Fallback keyword matched for 'assessment'. "
            context['intent_extraction'] = {
                'method': 'keyword',
                'intent': [agent_type],
                'confidence': 0.7,
                'reasoning': reasoning,
                'raw_response': None
            }
            context['clarification_needed'] = False
            context['clarification_prompt'] = None
            context['last_routed_agent'] = agent_type
            print("[ORCH DEBUG] Routing to agent (fallback): assessment")
            return self.assessment_agent, context, None
        elif any(word in message_lower for word in ['document', 'upload', 'file', 'analyze']):
            agent_type = 'document'
            reasoning += "Fallback keyword matched for 'document'. "
            context['intent_extraction'] = {
                'method': 'keyword',
                'intent': [agent_type],
                'confidence': 0.7,
                'reasoning': reasoning,
                'raw_response': None
            }
            context['clarification_needed'] = False
            context['clarification_prompt'] = None
            context['last_routed_agent'] = agent_type
            print("[ORCH DEBUG] Routing to agent (fallback): document")
            return self.document_agent, context, None
        elif any(word in message_lower for word in ['question', 'answer', 'continue', 'next']):
            agent_type = 'question'
            reasoning += "Fallback keyword matched for 'question'. "
            context['intent_extraction'] = {
                'method': 'keyword',
                'intent': [agent_type],
                'confidence': 0.7,
                'reasoning': reasoning,
                'raw_response': None
            }
            context['clarification_needed'] = False
            context['clarification_prompt'] = None
            context['last_routed_agent'] = agent_type
            print("[ORCH DEBUG] Routing to agent (fallback): question")
            return self.question_agent, context, None
        elif any(word in message_lower for word in ['status', 'progress', 'export', 'summary']):
            agent_type = 'status'
            reasoning += "Fallback keyword matched for 'status'. "
            context['intent_extraction'] = {
                'method': 'keyword',
                'intent': [agent_type],
                'confidence': 0.7,
                'reasoning': reasoning,
                'raw_response': None
            }
            context['clarification_needed'] = False
            context['clarification_prompt'] = None
            context['last_routed_agent'] = agent_type
            print("[ORCH DEBUG] Routing to agent (fallback): status")
            return self.status_agent, context, None
        # Step 4: No match, prompt for clarification
        clarification_prompt = (
            "I'm not sure what you want to do. "
            "Could you clarify if your request is about an assessment, document, question, or status?"
        )
        context['intent_extraction'] = {
            'method': 'none',
            'intent': None,
            'confidence': 0.0,
            'reasoning': reasoning,
            'raw_response': None
        }
        context['clarification_needed'] = True
        context['clarification_prompt'] = clarification_prompt
        print(f"[ORCH DEBUG] Routing to agent (fallback default): clarification needed")
        return None, context, clarification_prompt
    
    def _get_agent_by_type(self, agent_type: str) -> Agent:
        """Get agent instance by type."""
        agents = {
            'assessment': self.assessment_agent,
            'document': self.document_agent,
            'question': self.question_agent,
            'status': self.status_agent,
        }
        return agents.get(agent_type, self.assessment_agent)
    
    async def invoke_async(self, message: str, context: Dict[str, Any] = None) -> str:
        """
        Process message by routing to appropriate specialized agent, with enhanced support for list requests.
        Always uses and updates a shared context dict for Strands-agents best practice.
        """
        if context is None:
            context = {}
        
        # Check for session reset commands (safe word)
        msg_lower = message.lower().strip() if isinstance(message, str) else ""
        reset_keywords = ['reset', 'clear session', 'start over', 'restart', 'clear context', 'reset session', 'new session', 'fresh start']
        if any(keyword in msg_lower for keyword in reset_keywords):
            # Clear all context except session_id
            session_id = context.get('session_id', self.session_id)
            context.clear()
            context['session_id'] = session_id
            print(f"[ORCH DEBUG] Session context cleared by user request")
            return """🔄 Session reset successfully!

Your conversation context has been cleared. You can now start fresh.

Here's what you can do:
- Create a new TRA assessment
- List existing assessments
- Upload documents
- Ask questions about the system

How would you like to proceed?"""
        
        # Always try to extract assessment_id from message and update context
        import re
        if isinstance(message, str):
            match = re.search(r"TRA-\d{4}-[A-Z0-9]+", message, re.IGNORECASE)
            if match:
                context['assessment_id'] = match.group(0)
        print(f"[ORCH CONTEXT DEBUG] Initial context: {context}")
        print(f"[ORCH DEBUG] Orchestrator.invoke_async called with message: {message!r}, context: {context!r}")
        try:
            # --- Option selection logic: Check FIRST before other routing logic ---
            # This allows users to respond with "1", "2", etc. to presented options
            user_msg = message.strip().lower()
            last_msg = context.get('last_message', '')
            # Look for options in last system message - support both letter (A), B)) and numbered (1., 2.) formats
            letter_pattern = re.compile(r'([A-Z])\)\s+(.+?)(?=\n[A-Z]\)|$)', re.DOTALL)
            number_pattern = re.compile(r'(\d+)[\.\)]\s+(.+?)(?=\n\d+[\.\)]|$)', re.DOTALL)
            
            # Try letter-based options first
            options = dict(letter_pattern.findall(last_msg)) if last_msg else {}
            option_type = 'letter'
            
            # If no letter options, try numbered options
            if not options:
                number_matches = number_pattern.findall(last_msg)
                if number_matches:
                    options = {match[0]: match[1].strip() for match in number_matches}
                    option_type = 'number'
            
            # Acceptable user replies: 'Option B', 'B', 'b', '2', 'option 1', etc.
            # BUT: Don't intercept multi-selection like "1 and 3" - let the agent handle it
            selected_option = None
            is_multi_selection = bool(re.search(r'\d+\s+(and|,)\s+\d+', user_msg))
            
            if options and not is_multi_selection:
                if option_type == 'letter':
                    # Try to match 'option X' or just 'X'
                    m = re.match(r'(option\s*)?([a-zA-Z])\b', user_msg)
                    if m:
                        letter = m.group(2).upper()
                        if letter in options:
                            selected_option = letter
                    # Try to match by number (A=1, B=2, ...)
                    if not selected_option:
                        m2 = re.match(r'(option\s*)?(\d+)\b', user_msg)
                        if m2:
                            idx = int(m2.group(2)) - 1
                            letters = list(options.keys())
                            if 0 <= idx < len(letters):
                                selected_option = letters[idx]
                else:  # number type
                    # Try to match number directly (but only if it's a single number)
                    m = re.match(r'^(option\s*)?(\d+)$', user_msg.strip())
                    if m:
                        number = m.group(2)
                        if number in options:
                            selected_option = number
            if selected_option:
                # Log selection in context
                context['option_selected'] = selected_option
                context['option_selected_text'] = options[selected_option]
                print(f"[ORCH DEBUG] Option selection: '{selected_option}' -> '{options[selected_option]}'")
                # Route to agent based on option text (simple heuristic: look for keywords)
                opt_text = options[selected_option].lower()
                
                # NEW: Handle Option A - Upload documents for AI risk analysis
                if 'upload' in opt_text and ('document' in opt_text or 'ai-powered' in opt_text):
                    # Set context flag for document-based risk selection
                    context['risk_selection_mode'] = 'document'
                    context['waiting_for_documents'] = True
                    # Return instruction message (no agent call needed)
                    return "📄 Please upload 1 project document (architecture, requirements, or security doc) using the upload button."
                
                # NEW: Handle Option C - Answer AI questions to identify areas
                elif 'answer' in opt_text and 'ai question' in opt_text and 'identify' in opt_text:
                    # Set context flag for qualifying questions mode
                    context['qualifying_questions_mode'] = True
                    context['current_qualifying_question'] = 'C-01'  # Start with first question
                    context['qualifying_answers'] = {}
                    # Route to Question Agent to handle qualifying questions
                    target_agent = self.question_agent
                    # Pass a special message to start qualifying questions
                    result = await target_agent.invoke_async("start qualifying questions", context)
                    if isinstance(result, dict):
                        for k, v in result.items():
                            if k not in ("success", "message", "error"):
                                context[k] = v
                        if 'last_message' in context:
                            return context['last_message']
                        if 'message' in result:
                            return result['message']
                        return str(result)
                    return str(result)
                # NEW: Handle Option A - Start Answering Questions (after qualifying questions)
                elif 'start answering questions' in opt_text.lower() or ('begin answering' in opt_text.lower() and 'questions' in opt_text.lower()):
                    # User wants to start answering questions for identified risk areas
                    # Check if there are multiple risk areas - if so, show selection buttons
                    from backend.tools.assessment_tools import get_assessment
                    assessment_id = context.get('assessment_id')
                    if assessment_id:
                        assessment_result = await get_assessment(assessment_id, context)
                        if assessment_result.get('success') and 'assessment' in assessment_result:
                            assessment = assessment_result['assessment']
                            active_risk_areas = assessment.get('active_risk_areas', [])
                            
                            if len(active_risk_areas) > 1:
                                # Multiple risk areas - route to Assessment Agent which will show buttons
                                target_agent = self.assessment_agent
                                # Pass a message that will trigger the risk area button display
                                result = await target_agent.invoke_async("show risk area selection", context)
                            elif len(active_risk_areas) == 1:
                                # Single risk area - route directly to Question Agent
                                target_agent = self.question_agent
                                result = await target_agent.invoke_async("start questions", context)
                            else:
                                # No risk areas - shouldn't happen but handle gracefully
                                return "No risk areas have been identified yet. Please complete the qualifying questions first."
                        else:
                            return "Could not load assessment details. Please try again."
                    else:
                        return "No assessment ID found. Please create or load an assessment first."
                # Existing routing for other options
                elif 'document' in opt_text:
                    target_agent = self.document_agent
                elif 'standard risk' in opt_text or 'select' in opt_text:
                    target_agent = self.assessment_agent
                elif 'question' in opt_text:
                    target_agent = self.question_agent
                else:
                    # Default to question agent if "question" is in the option
                    target_agent = self.question_agent
                # Pass the option text as the message to the agent
                result = await target_agent.invoke_async(options[selected_option], context)
                if isinstance(result, dict):
                    for k, v in result.items():
                        if k not in ("success", "message", "error"):
                            context[k] = v
                    if 'last_message' in context:
                        return context['last_message']
                    if 'message' in result:
                        return result['message']
                    return str(result)
                return str(result)
            
            # Enhanced: Recognize list/enumeration requests
            msg_lower = message.lower() if isinstance(message, str) else ""
            if re.search(r"\b(list|show|display|enumerate|get all)\s+(assessments?|documents?|files?|knowledge\s*base|kb\s*items?)\b", msg_lower):
                # Assessments
                if re.search(r"assessments?", msg_lower):
                    from backend.tools.assessment_tools import list_assessments
                    state = None
                    match = re.search(r"status\s+(\w+)", msg_lower)
                    if match:
                        state = match.group(1)
                    # Only pass session_id if user explicitly requests session-specific ("my assessments", etc.)
                    session_specific = False
                    if re.search(r"my|this session|current session", msg_lower):
                        session_specific = True
                    # For global listing (default), do not pass session_id at all
                    result = await list_assessments(
                        session_id=self.session_id if session_specific else None,
                        status_filter=state
                    )
                    context['last_list_assessments'] = result
                    if result.get("success"):
                        if result["count"] == 0:
                            return "No assessments found."
                        lines = [f"Assessments ({result['count']}):"]
                        for a in result["assessments"]:
                            lines.append(f"- {a['assessment_id']} | {a.get('title','')} | State: {a.get('current_state','')} | Progress: {a.get('completion_percentage',0)}% | Created: {a.get('created_at','')}")
                        return "\n".join(lines)
                    else:
                        return f"Could not list assessments: {result.get('error','Unknown error')}"
                # Documents
                if re.search(r"documents?|files?", msg_lower):
                    from backend.tools.status_tools import list_documents
                    result = await list_documents()
                    context['last_list_documents'] = result
                    if result.get("success"):
                        if result["count"] == 0:
                            return "No documents found."
                        lines = [f"Documents ({result['count']}):"]
                        for d in result["documents"]:
                            lines.append(f"- {d['document_id']} | {d.get('filename','')} | Assessment: {d.get('assessment_id','')} | Uploaded: {d.get('uploaded_at','')} | Status: {d.get('status','')}")
                        return "\n".join(lines)
                    else:
                        return f"Could not list documents: {result.get('error','Unknown error')}"
                # Knowledge Base Items
                if re.search(r"knowledge\s*base|kb\s*items?", msg_lower):
                    from backend.tools.status_tools import list_kb_items
                    result = await list_kb_items()
                    context['last_list_kb_items'] = result
                    if result.get("success"):
                        if result["count"] == 0:
                            return "No knowledge base items found."
                        lines = [f"Knowledge Base Items ({result['count']}):"]
                        for k in result["kb_items"]:
                            lines.append(f"- {k['document_id']} | {k.get('filename','')} | Assessment: {k.get('assessment_id','')} | Uploaded: {k.get('uploaded_at','')} | Status: {k.get('status','')}")
                        return "\n".join(lines)
                    else:
                        return f"Could not list knowledge base items: {result.get('error','Unknown error')}"
                return "Listing for this entity type is not yet supported. You can list assessments, documents, or knowledge base items, or request details for a specific item."
            # Determine which agent should handle this
            target_agent, context, clarification_prompt = await self._determine_agent(message, context)
            
            # Special handling: if user says "add more risk areas" and we have assessment_id in context,
            # ensure it stays in context and route to assessment agent
            msg_lower = message.lower() if isinstance(message, str) else ""
            if re.search(r'\b(add|select)\s+(more|another|additional)?\s*risk\s*area', msg_lower):
                if context.get('assessment_id') and not target_agent:
                    target_agent = self.assessment_agent
                    context['last_routed_agent'] = 'assessment'
                    print(f"[ORCH DEBUG] Special routing: add more risk areas with assessment_id={context.get('assessment_id')}")
            # --- PATCH: If multi-intent (assessment, question) and assessment_id is present, default to QuestionAgent ---
            if clarification_prompt and context.get('assessment_id'):
                # If SLM returned multi-intent and we have assessment_id, prefer QuestionAgent for question-related requests
                last_intent = context.get('intent_extraction', {}).get('intent', [])
                if isinstance(last_intent, list) and 'question' in last_intent:
                    target_agent = self.question_agent
                    clarification_prompt = None
            if clarification_prompt:
                return clarification_prompt
            if target_agent is None:
                return "I'm not sure what you want to do. Please clarify if your request is about an assessment, document, question, or status."
            print(f"[ORCH DEBUG] Routing to agent: {type(target_agent).__name__}")
            # PATCH: Always inject last loaded assessment_id and risk_area into context if present
            if 'assessment' in context:
                a = context['assessment']
                if a.get('assessment_id'):
                    context['assessment_id'] = a['assessment_id']
                if a.get('active_risk_areas'):
                    context['active_risk_areas'] = a['active_risk_areas']
            # Guarantee assessment_id for QuestionAgent
            from .agents.question_agent import QuestionAgent
            if isinstance(target_agent, QuestionAgent):
                if not context.get('assessment_id'):
                    # Try to get from last assessment in context
                    if 'assessment' in context and context['assessment'].get('assessment_id'):
                        context['assessment_id'] = context['assessment']['assessment_id']
                print(f"[ORCH CONTEXT DEBUG] Passing to QuestionAgent: {context}")
            # Delegate to agent, always passing context
            result = await target_agent.invoke_async(message, context)
            print(f"[ORCH CONTEXT DEBUG] After agent call, context: {context}")
            
            # Extract assessment_id from result if present (for context preservation)
            result_str = str(result)
            if not context.get('assessment_id'):
                tra_match = re.search(r'TRA-\d{4}-[A-Z0-9]+', result_str)
                if tra_match:
                    context['assessment_id'] = tra_match.group(0)
                    print(f"[ORCH DEBUG] Extracted assessment_id from result: {context['assessment_id']}")
            
            # If agent returns a dict with context keys, merge them into context
            if isinstance(result, dict):
                for k, v in result.items():
                    # Only update context for non-message keys
                    if k not in ("success", "message", "error"):
                        context[k] = v
                # --- CONTEXT-AWARE NEXT-STEP LOGIC AFTER ASSESSMENT LOAD ---
                # If routed to AssessmentAgent and assessment is loaded, check risk areas and auto-route if needed
                from .agents.assessment_agent import AssessmentAgent
                if isinstance(target_agent, AssessmentAgent):
                    assessment = context.get('assessment')
                    if assessment and 'active_risk_areas' in assessment:
                        active_risk_areas = assessment['active_risk_areas']
                        if len(active_risk_areas) == 1:
                            # Auto-route to QuestionAgent to start questions for the only risk area
                            from .agents.question_agent import QuestionAgent
                            q_agent = self.question_agent
                            # Compose a message to load questions for the risk area
                            ra_id = active_risk_areas[0]
                            msg = f"start questions for risk area {ra_id}"
                            # Merge assessment_id into context for QuestionAgent
                            context['assessment_id'] = assessment.get('assessment_id')
                            q_result = await q_agent.invoke_async(msg, context)
                            # Merge context keys from q_result if dict
                            if isinstance(q_result, dict):
                                for k, v in q_result.items():
                                    if k not in ("success", "message", "error"):
                                        context[k] = v
                                if 'last_message' in context:
                                    return context['last_message']
                                if 'message' in q_result:
                                    return q_result['message']
                                return str(q_result)
                            return str(q_result)
                        elif len(active_risk_areas) == 0:
                            # No risk areas, prompt to add
                            return context.get('last_message', 'No risk areas attached. Please add a risk area to begin.')
                        # If multiple, let AssessmentAgent's message prompt user to select
                # Prefer returning last_message if present
                if 'last_message' in context:
                    return context['last_message']
                if 'message' in result:
                    return result['message']
                return str(result)
            # Fallback: just return string result
            return str(result)
        except Exception as e:
            print(f"[ORCH DEBUG] Orchestrator error: {e}")
            return f"I encountered an error: {str(e)}. Please try rephrasing your request."
    
    async def stream_async(self, message: str, context: Dict[str, Any] = None) -> AsyncIterator[Dict[str, Any]]:
        """
        Process message with streaming support.
        
        Args:
            message: User message
            context: Optional context dictionary
            
        Yields:
            Event dictionaries with streaming data
        """
        try:
            # Determine which agent should handle this
            target_agent = self._determine_agent(message)
            
            # Stream from specialist agent
            async for event in target_agent.stream_async(message, context):
                yield event
                
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "message": "An error occurred during processing"
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status from all agents."""
        return {
            "system": "Enterprise TRA Multi-Agent",
            "version": "1.0.0",
            "framework": "Strands Agents 1.x",
            "session_id": self.session_id,
            "architecture": "Orchestrator + 4 Specialized Agents",
            "agents": {
                "orchestrator": "active",
                "assessment": self.assessment_agent.get_status(),
                "document": self.document_agent.get_status(),
                "question": self.question_agent.get_status(),
                "status": self.status_agent.get_status(),
            }
        }


def create_enterprise_agent(session_id: str = None) -> EnterpriseOrchestratorAgent:
    """
    Factory function to create Enterprise TRA Orchestrator.
    
    Args:
        session_id: Optional session identifier
        
    Returns:
        Configured EnterpriseOrchestratorAgent instance
    """
    return EnterpriseOrchestratorAgent(session_id=session_id)
