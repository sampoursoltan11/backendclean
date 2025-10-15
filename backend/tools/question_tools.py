import logging

from strands import tool
# Risk area management tools (delegate to assessment_tools)
from backend.tools.assessment_tools import add_risk_area as _add_risk_area, remove_risk_area as _remove_risk_area

logger = logging.getLogger(__name__)

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
        risk_area_id: ID of the risk area to add
        context: Shared context dictionary
    Returns:
        Dictionary with update status
    """
    return await _add_risk_area(assessment_id, risk_area_id, context)

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
    return await _remove_risk_area(assessment_id, risk_area_id, context)
"""
Question Flow Tools - Strands 1.x Compatible
Tools for TRA questionnaire management and routing
"""

import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
from strands import tool

from backend.core.config import get_settings
from backend.services.dynamodb_service import DynamoDBService


# Cache for decision tree
_decision_tree: Optional[Dict[str, Any]] = None
_db_service: Optional[DynamoDBService] = None

def get_decision_tree() -> Dict[str, Any]:
    """Load and cache decision tree configuration (decision_tree2.yaml format)."""
    global _decision_tree

    if _decision_tree is None:
        try:
            settings = get_settings()
            config_path = Path(settings.decision_tree_config_path)

            if not config_path.is_absolute():
                # Make relative to project root
                project_root = Path(__file__).parent.parent.parent
                config_path = project_root / config_path

            with open(config_path, 'r', encoding='utf-8') as f:
                raw_tree = yaml.safe_load(f)

            # Build flat questions list from decision_tree2.yaml nested structure
            all_questions = []

            # Add qualifying questions
            qualifying = raw_tree.get('qualifying_questions', [])
            for q in qualifying:
                q_copy = q.copy()
                q_copy['risk_area'] = 'qualifying'
                # Normalize 'response_type' to 'type'
                if 'response_type' in q_copy:
                    response_type = q_copy['response_type']
                    # Map response types to question types
                    type_mapping = {
                        'Yes/No': 'select',
                        'free-text': 'text',
                        'text': 'text',
                        'textarea': 'textarea',
                        'select': 'select',
                        'multiselect': 'multiselect'
                    }
                    q_copy['type'] = type_mapping.get(response_type, 'text')
                    # Add Yes/No options if response_type is Yes/No
                    if response_type == 'Yes/No' and 'options' not in q_copy:
                        q_copy['options'] = [
                            {'label': 'Yes', 'value': 'Yes'},
                            {'label': 'No', 'value': 'No'}
                        ]
                all_questions.append(q_copy)

            # Add risk area questions
            risk_areas = raw_tree.get('risk_areas', {})
            if isinstance(risk_areas, dict):
                for area_id, area_data in risk_areas.items():
                    questions = area_data.get('questions', [])
                    for q in questions:
                        q_copy = q.copy()
                        q_copy['risk_area'] = area_id
                        # Normalize 'response_type' to 'type'
                        if 'response_type' in q_copy:
                            response_type = q_copy['response_type']
                            type_mapping = {
                                'Yes/No': 'select',
                                'free-text': 'text',
                                'text': 'text',
                                'textarea': 'textarea',
                                'select': 'select',
                                'multiselect': 'multiselect'
                            }
                            q_copy['type'] = type_mapping.get(response_type, 'text')
                            # Add Yes/No options if response_type is Yes/No
                            if response_type == 'Yes/No' and 'options' not in q_copy:
                                q_copy['options'] = [
                                    {'label': 'Yes', 'value': 'Yes'},
                                    {'label': 'No', 'value': 'No'}
                                ]
                        all_questions.append(q_copy)

            # Add normalized questions to the tree
            raw_tree['questions'] = all_questions
            _decision_tree = raw_tree

        except Exception as e:
            # Return empty structure if config not found
            _decision_tree = {"questions": [], "risk_areas": {}}

    return _decision_tree


def get_db_service() -> DynamoDBService:
    """Get singleton DynamoDB service."""
    global _db_service
    if _db_service is None:
        _db_service = DynamoDBService()
    return _db_service


@tool
async def question_flow(
    assessment_id: str,
    risk_area: str = None,
    answer: str = None
) -> dict:
    """
    Unified question flow: Get next question OR save answer and get next.
    
    USE THIS TOOL FOR ALL QUESTION INTERACTIONS:
    - To get first/next question: Call with answer=None
    - To save answer and continue: Call with answer="user's answer"
    
    Args:
        assessment_id: ID of the assessment
        answer: User's answer (None to just get next question)
    
    Returns:
        Dictionary with question (and save confirmation if answer provided)
    """
    try:
        db = get_db_service()
        # Get assessment
        assessment = await db.get_assessment(assessment_id)
        if not assessment:
            return {
                "success": False,
                "error": f"Assessment {assessment_id} not found"
            }
        # Get active risk areas to validate selection
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
        
        # Use risk_area for filtering questions/answers
        if not risk_area:
            risk_area = assessment.get('current_risk_area')
        
        # Validate that selected risk_area is in active_risk_areas
        if risk_area and risk_area not in active_risk_areas:
            # Invalid risk area, use first attached
            risk_area = active_risk_areas[0] if active_risk_areas else None
        
        if not risk_area:
            # Fallback: use first attached
            risk_area = active_risk_areas[0] if active_risk_areas else None
        
        if not risk_area:
            return {
                "success": False,
                "error": "No risk area specified and no active risk areas in assessment"
            }
        
        # Persist current risk_area
        await db.update_assessment(assessment_id, {"current_risk_area": risk_area})
        # Prepare answers dict per risk_area
        all_answers = assessment.get('answers_by_risk_area', {})
        answers = all_answers.get(risk_area, {})
        # If answer provided, save it first
        if answer is not None:
            question_id = assessment.get('current_question_id')
            if not question_id:
                return {
                    "success": False,
                    "error": "No active question to answer. Call with answer=None first."
                }
            decision_tree = get_decision_tree()

            # Get questions for this risk area - handle both decision tree formats
            # Format 1: Global questions list with risk_area field
            questions = [q for q in decision_tree.get("questions", []) if q.get("risk_area") == risk_area]

            # Format 2: Questions embedded in risk_areas dict (decision_tree3.yaml)
            if not questions:
                risk_areas_data = decision_tree.get("risk_areas", {})
                if isinstance(risk_areas_data, dict) and risk_area in risk_areas_data:
                    questions = risk_areas_data[risk_area].get("questions", [])

            # STEP 1: VALIDATE
            question = next((q for q in questions if q.get("id") == question_id), None)
            if not question:
                return {
                    "success": False,
                    "error": f"Question {question_id} not found"
                }
            # Validate answer
            question_type = question.get("type", "text")
            normalized_answer = answer
            if question.get("required", True) and (answer == "" or answer == []):
                return {
                    "success": False,
                    "error": "This question is required"
                }
            # Handle multiselect normalization
            if question_type == "multiselect":
                if isinstance(answer, str):
                    answer_list = [a.strip() for a in answer.split(',')]
                elif isinstance(answer, list):
                    answer_list = answer
                else:
                    answer_list = [str(answer)]
                
                options = question.get("options", [])
                normalized_answers = []
                for ans in answer_list:
                    ans_lower = str(ans).lower().strip()
                    for opt in options:
                        if (opt.get("value", "").lower() == ans_lower or 
                            opt.get("label", "").lower() == ans_lower):
                            normalized_answers.append(opt.get("value"))
                            break
                normalized_answer = normalized_answers
            
            # Handle select normalization
            elif question_type == "select":
                options = question.get("options", [])
                answer_lower = str(answer).lower().strip()
                for opt in options:
                    if (opt.get("value", "").lower() == answer_lower or 
                        opt.get("label", "").lower() == answer_lower):
                        normalized_answer = opt.get("value")
                        break
            
            # STEP 2: SAVE
            answers[question_id] = normalized_answer

            # STEP 2.5: Auto-trigger risk areas for qualifying questions (C-0X)
            if question_id.startswith("C-") and str(normalized_answer).lower() in ['yes', 'y', 'true']:
                # Check if this is a triggering question
                decision_tree = get_decision_tree()
                qual_questions = decision_tree.get('qualifying_questions', [])
                qual_q = next((q for q in qual_questions if q.get('id') == question_id), None)

                if qual_q and 'on_yes' in qual_q:
                    on_yes = qual_q['on_yes']
                    if on_yes.get('action') == 'show_all_questions':
                        risk_area_name = on_yes.get('risk_area')
                        # Map risk area name to ID
                        risk_area_map = {
                            'Third Party': 'third_party',
                            'Data Privacy': 'data_privacy',
                            'Artificial Intelligence': 'artificial_intelligence',
                            'AI': 'artificial_intelligence',
                            'Intellectual Property': 'intellectual_property',
                            'IP': 'intellectual_property'
                        }
                        risk_area_id = risk_area_map.get(risk_area_name, risk_area_name.lower().replace(' ', '_'))

                        # Auto-add risk area if not already present
                        if risk_area_id not in active_risk_areas:
                            active_risk_areas.append(risk_area_id)
                            await db.update_assessment(assessment_id, {
                                'active_risk_areas': active_risk_areas
                            })
                            logger.info(f"Auto-trigger: Added {risk_area_id} based on {question_id}=Yes")
            # Calculate OVERALL progress across ALL active risk areas (not just current one)
            # Use smart counting with show_questions logic
            decision_tree = get_decision_tree()
            assessment = await db.get_assessment(assessment_id)
            active_risk_areas = assessment.get('active_risk_areas', [risk_area])

            # Use _count_applicable_questions for each risk area (handles show_questions, depends_on, etc.)
            total_applicable = 0
            total_answered = 0

            for area_id in active_risk_areas:
                area_answers = all_answers.get(area_id, {})
                applicable, answered = _count_applicable_questions(area_id, area_answers, decision_tree)
                total_applicable += applicable
                total_answered += answered

            completion_percentage = round((total_answered / total_applicable) * 100, 1) if total_applicable > 0 else 0

            # Update assessment with answers and OVERALL completion percentage
            all_answers[risk_area] = answers
            await db.update_assessment(assessment_id, {
                "answers_by_risk_area": all_answers,
                "completion_percentage": completion_percentage,
                "current_question_id": None,
                "current_risk_area": risk_area
            })
            saved_message = f"✓ Answer '{answer}' saved. Overall Progress: {completion_percentage}%\n\n"
        else:
            # No answer provided, just getting next question
            saved_message = ""
        # STEP 3: GET NEXT QUESTION (with decision_tree2.yaml logic)
        decision_tree = get_decision_tree()

        # Get questions for this risk area - handle both decision tree formats
        # Format 1: Global questions list with risk_area field
        questions = [q for q in decision_tree.get("questions", []) if q.get("risk_area") == risk_area]

        # Format 2: Questions embedded in risk_areas dict (decision_tree3.yaml)
        if not questions:
            risk_areas_data = decision_tree.get("risk_areas", {})
            if isinstance(risk_areas_data, dict) and risk_area in risk_areas_data:
                questions = risk_areas_data[risk_area].get("questions", [])

        # Build skip list from all answered questions
        skipped_question_ids = []
        for answered_id, answered_value in answers.items():
            skipped = _get_skipped_questions(answered_id, answered_value, decision_tree)
            skipped_question_ids.extend(skipped)

        # Store skip list in assessment for tracking
        await db.update_assessment(assessment_id, {
            "skipped_questions": skipped_question_ids
        })

        next_question = None
        for q in questions:
            # Use comprehensive question filtering (pass all_questions for show_questions logic)
            if _should_show_question(q, answers, skipped_question_ids, all_questions=questions):
                q_id = q.get("id")
                # Store this as current question
                await db.update_assessment(assessment_id, {
                    "current_question_id": q_id,
                    "current_risk_area": risk_area
                })
                next_question = {
                    "question_id": q_id,
                    "question": q.get("question", ""),
                    "type": q.get("type", "text"),
                    "required": q.get("required", True),
                    "options": q.get("options", []),
                    "help_text": q.get("help_text", ""),
                    "risk_area": q.get("risk_area", risk_area),
                    "level": q.get("level", "L2")
                }
                break

        if not next_question:
            return {
                "success": True,
                "completed": True,
                "message": saved_message + "All questions answered!"
            }
        return {
            "success": True,
            "completed": False,
            "message": saved_message,
            "next_question": next_question
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "next_question": None
        }


@tool
async def save_answer(
    assessment_id: str,
    question_id: str,
    answer: Any
) -> dict:
    """
    Save an answer to a question in the assessment.
    CRITICAL: This tool MUST be called after validating an answer to persist it.
    
    Args:
        assessment_id: ID of the assessment
        question_id: ID of the question being answered
        answer: The answer to save
    
    Returns:
        Dictionary with save confirmation
    """
    try:
        db = get_db_service()
        
        # Get current assessment
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            return {
                "success": False,
                "error": f"Assessment {assessment_id} not found"
            }
        
        # Get current answers dict
        current_answers = assessment.get('answers', {})
        
        # Add/update this answer
        current_answers[question_id] = answer
        
        # Calculate new progress
        decision_tree = get_decision_tree()
        questions = decision_tree.get("questions", [])
        
        # Count applicable questions
        applicable_questions = []
        for q in questions:
            conditions = q.get("conditions", [])
            if not conditions or _evaluate_conditions(conditions, current_answers):
                applicable_questions.append(q)
        
        total_questions = len(applicable_questions)
        answered_questions = len([
            q for q in applicable_questions 
            if q.get("id") in current_answers
        ])
        
        completion_percentage = round((answered_questions / total_questions) * 100, 1) if total_questions > 0 else 0
        
        # Update assessment in DynamoDB
        updates = {
            "answers": current_answers,
            "completion_percentage": completion_percentage
        }
        
        await db.update_assessment(assessment_id, updates)
        
        return {
            "success": True,
            "question_id": question_id,
            "answer_saved": True,
            "total_answered": answered_questions,
            "completion_percentage": completion_percentage,
            "message": f"Answer saved. Progress: {completion_percentage}%"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to save answer"
        }


@tool
async def get_next_question(
    assessment_id: str
) -> dict:
    """
    Get the next unanswered question and set it as current question.
    This tool STORES the question_id so answer_question knows which question to save.
    
    Args:
        assessment_id: ID of the assessment
    
    Returns:
        Dictionary with next question details or completion status
    """
    try:
        db = get_db_service()
        
        # Get assessment with current answers
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            return {
                "completed": False,
                "error": f"Assessment {assessment_id} not found"
            }
        
        current_answers = assessment.get('answers', {})
        
        decision_tree = get_decision_tree()
        questions = decision_tree.get("questions", [])
        
        if not questions:
            return {
                "completed": False,
                "error": "No questions available in decision tree"
            }
        
        # Find first unanswered question that meets conditions
        for question in questions:
            question_id = question.get("id")
            
            # Skip if already answered
            if question_id in current_answers:
                continue
            
            # Check conditions (if any)
            conditions = question.get("conditions", [])
            if conditions:
                if not _evaluate_conditions(conditions, current_answers):
                    continue
            
            # Store this as current question
            await db.update_assessment(assessment_id, {
                "current_question_id": question_id
            })
            
            # This is the next question
            return {
                "completed": False,
                "question_id": question_id,
                "question": question.get("question", ""),
                "type": question.get("type", "text"),
                "required": question.get("required", True),
                "options": question.get("options", []),
                "help_text": question.get("help_text", ""),
                "risk_area": question.get("risk_area", "General"),
                "validation": question.get("validation", {})
            }
        
        # All questions answered
        return {
            "completed": True,
            "message": "All questions answered!",
            "total_questions": len(questions),
            "answered_questions": len(current_answers),
            "completion_percentage": assessment.get('completion_percentage', 100)
        }
        
    except Exception as e:
        return {
            "completed": False,
            "error": str(e)
        }


def _evaluate_conditions(conditions: List[Dict[str, Any]], answers: Dict[str, Any]) -> bool:
    """
    Evaluate if conditions are met based on current answers.
    Legacy function for backward compatibility.

    Args:
        conditions: List of condition dictionaries
        answers: Current answers

    Returns:
        True if all conditions are met, False otherwise
    """
    for condition in conditions:
        question_id = condition.get("question_id")
        operator = condition.get("operator")
        value = condition.get("value")

        if question_id not in answers:
            return False

        answer_value = answers[question_id]

        if operator == "equals":
            if answer_value != value:
                return False
        elif operator == "contains":
            if value not in str(answer_value):
                return False
        elif operator == "not_equals":
            if answer_value == value:
                return False
        elif operator == "greater_than":
            if not (answer_value > value):
                return False
        elif operator == "less_than":
            if not (answer_value < value):
                return False

    return True


def _evaluate_depends_on(question: Dict[str, Any], answers: Dict[str, Any]) -> bool:
    """
    Evaluate depends_on condition from decision_tree2.yaml format.

    Args:
        question: Question dictionary with depends_on field
        answers: Current answers

    Returns:
        True if dependency is met, False otherwise
    """
    depends_on = question.get("depends_on")
    if not depends_on:
        return True  # No dependency, always show

    # depends_on format: {question_id: "DP-02", answer: "Yes"}
    required_question_id = depends_on.get("question_id")
    required_answer = depends_on.get("answer")

    if not required_question_id:
        return True

    # Check if parent question has been answered with the required value
    actual_answer = answers.get(required_question_id)

    if actual_answer is None:
        return False  # Parent not answered yet

    # Compare answers (case-insensitive for strings)
    if isinstance(actual_answer, str) and isinstance(required_answer, str):
        return actual_answer.lower() == required_answer.lower()

    return actual_answer == required_answer


def _get_skipped_questions(question_id: str, answer: str, decision_tree: Dict[str, Any]) -> List[str]:
    """
    Get list of questions to skip based on on_yes/on_no skip logic.

    Args:
        question_id: ID of the question that was answered
        answer: The answer given
        decision_tree: Full decision tree

    Returns:
        List of question IDs to skip
    """
    # Find the question in the tree
    all_questions = decision_tree.get("questions", [])
    question = next((q for q in all_questions if q.get("id") == question_id), None)

    if not question:
        return []

    skip_questions = []

    # Check on_yes skip logic
    if answer and str(answer).lower() in ['yes', 'y', 'true']:
        on_yes = question.get("on_yes", {})
        if on_yes.get("action") == "skip_questions":
            skip_questions.extend(on_yes.get("skip_questions", []))

    # Check on_no skip logic
    if answer and str(answer).lower() in ['no', 'n', 'false']:
        on_no = question.get("on_no", {})
        if on_no.get("action") == "skip_questions":
            skip_questions.extend(on_no.get("skip_questions", []))

    return skip_questions


def _check_show_questions_dependency(question: Dict[str, Any], all_questions: List[Dict[str, Any]], answers: Dict[str, Any]) -> bool:
    """
    Check if question should be shown based on show_questions dependency logic (decision_tree3.yaml).

    A question with ID X is shown only if:
    - It's in the show_questions list of an answered parent question, OR
    - No other question lists it in their show_questions (it's independently shown)

    Args:
        question: Question to check
        all_questions: All questions in the risk area
        answers: Current answers

    Returns:
        True if question should be shown based on show_questions logic
    """
    q_id = question.get("id")

    # Find all questions that have q_id in their show_questions list
    parent_questions = []
    for q in all_questions:
        show_list = q.get("show_questions", [])
        if q_id in show_list:
            parent_questions.append(q.get("id"))

    # If no parents list this question, it can be shown independently
    if not parent_questions:
        return True

    # If parents exist, at least one must be answered
    for parent_id in parent_questions:
        if parent_id in answers:
            return True

    # No answered parent found
    return False


def _should_show_question(question: Dict[str, Any], answers: Dict[str, Any], skipped_ids: List[str], all_questions: List[Dict[str, Any]] = None) -> bool:
    """
    Determine if a question should be shown based on all rules.

    Args:
        question: Question dictionary
        answers: Current answers
        skipped_ids: List of question IDs that have been skipped
        all_questions: All questions in risk area (needed for show_questions logic)

    Returns:
        True if question should be shown, False otherwise
    """
    q_id = question.get("id")

    # 1. Skip if already answered
    if q_id in answers:
        return False

    # 2. Skip if in skip list
    if q_id in skipped_ids:
        return False

    # 3. Check depends_on (decision_tree2.yaml format)
    if not _evaluate_depends_on(question, answers):
        return False

    # 4. Check legacy conditions (backward compatibility)
    conditions = question.get("conditions", [])
    if conditions and not _evaluate_conditions(conditions, answers):
        return False

    # 5. Check show_questions dependency (decision_tree3.yaml format)
    if all_questions:
        if not _check_show_questions_dependency(question, all_questions, answers):
            return False

    # All checks passed - question should be shown
    return True


def _count_applicable_questions(risk_area: str, answers: Dict[str, Any], decision_tree: Dict[str, Any]) -> tuple:
    """
    Count only the questions that are applicable based on decision tree logic (skips, dependencies).
    This provides accurate completion tracking.

    Args:
        risk_area: Risk area ID
        answers: Current answers for this risk area
        decision_tree: Full decision tree

    Returns:
        Tuple of (applicable_count, answered_count)

    Note: This function is exported and used by other modules for smart completion tracking.
    """
    # Get all questions for this risk area
    # Format 1: Global questions list with risk_area field
    questions = [q for q in decision_tree.get("questions", []) if q.get("risk_area") == risk_area]

    # Format 2: Questions embedded in risk_areas dict (decision_tree3.yaml)
    if not questions:
        risk_areas_data = decision_tree.get("risk_areas", {})
        if isinstance(risk_areas_data, dict) and risk_area in risk_areas_data:
            questions = risk_areas_data[risk_area].get("questions", [])

    # Build skip list from all answered questions
    skipped_question_ids = []
    for answered_id, answered_value in answers.items():
        skipped = _get_skipped_questions(answered_id, answered_value, decision_tree)
        skipped_question_ids.extend(skipped)

    # Count only applicable questions (not skipped, dependencies met, show_questions logic)
    applicable_count = 0
    answered_count = 0

    for q in questions:
        q_id = q.get("id")

        # Skip if already answered (for counting purposes, we still want to count it)
        is_answered = q_id in answers

        # Skip if in skip list
        if q_id in skipped_question_ids:
            continue

        # Check depends_on - if parent not answered yet, don't count it
        depends_on = q.get("depends_on")
        if depends_on:
            parent_id = depends_on.get("question_id")
            if parent_id and parent_id not in answers:
                # Parent not answered yet, can't determine if this will show
                continue
            # Parent answered, check if condition is met
            if not _evaluate_depends_on(q, answers):
                continue

        # Check legacy conditions
        conditions = q.get("conditions", [])
        if conditions:
            # If any condition references unanswered questions, skip for now
            can_evaluate = all(c.get("question_id") in answers for c in conditions)
            if not can_evaluate:
                continue
            if not _evaluate_conditions(conditions, answers):
                continue

        # Check show_questions dependency (decision_tree3.yaml format)
        if not _check_show_questions_dependency(q, questions, answers):
            continue

        # This question is applicable
        applicable_count += 1
        if is_answered:
            answered_count += 1

    return applicable_count, answered_count


@tool
def validate_answer(
    question_id: str,
    answer: Any
) -> dict:
    """
    Validate an answer against question requirements.
    NOTE: This only validates - use save_answer to persist the answer.
    
    Args:
        question_id: ID of the question being answered
        answer: The provided answer
    
    Returns:
        Dictionary with validation result
    """
    try:
        decision_tree = get_decision_tree()
        questions = decision_tree.get("questions", [])
        
        # Find the question
        question = next((q for q in questions if q.get("id") == question_id), None)
        
        if not question:
            return {
                "valid": False,
                "error": f"Question {question_id} not found"
            }
        
        question_type = question.get("type", "text")
        
        # Check if required and empty
        if question.get("required", True):
            if answer is None or answer == "" or answer == []:
                return {
                    "valid": False,
                    "error": "This question is required"
                }
        
        # For multiselect, handle list or comma-separated string
        if question_type == "multiselect":
            # Convert to list if string
            if isinstance(answer, str):
                # Handle comma-separated or single value
                answer_list = [a.strip() for a in answer.split(',')]
            elif isinstance(answer, list):
                answer_list = answer
            else:
                answer_list = [str(answer)]
            
            # Get valid option values
            options = question.get("options", [])
            valid_values = [opt.get("value") for opt in options]
            
            # Normalize answer values (lowercase, match by label too)
            normalized_answers = []
            for ans in answer_list:
                ans_lower = str(ans).lower().strip()
                # Try to match by value or label
                matched = False
                for opt in options:
                    if (opt.get("value", "").lower() == ans_lower or 
                        opt.get("label", "").lower() == ans_lower):
                        normalized_answers.append(opt.get("value"))
                        matched = True
                        break
                if not matched and ans_lower:  # If no match but not empty
                    return {
                        "valid": False,
                        "error": f"Invalid option: {ans}",
                        "valid_options": [opt.get("label") for opt in options]
                    }
            
            if not normalized_answers:
                return {
                    "valid": False,
                    "error": "Please select at least one option",
                    "valid_options": [opt.get("label") for opt in options]
                }
            
            return {
                "valid": True,
                "normalized_answer": normalized_answers,
                "message": "Valid answer"
            }
        
        # For select type, validate single option
        if question_type == "select":
            options = question.get("options", [])
            valid_values = [opt.get("value") for opt in options]
            
            # Try to match by value or label (case insensitive)
            answer_lower = str(answer).lower().strip()
            for opt in options:
                if (opt.get("value", "").lower() == answer_lower or 
                    opt.get("label", "").lower() == answer_lower):
                    return {
                        "valid": True,
                        "normalized_answer": opt.get("value"),
                        "message": "Valid answer"
                    }
            
            return {
                "valid": False,
                "error": f"Invalid option: {answer}",
                "valid_options": [opt.get("label") for opt in options]
            }
        
        # Get validation rules for text/textarea
        validation = question.get("validation", {})
        
        # Validate minimum length
        min_length = validation.get("min_length")
        if min_length and len(str(answer)) < min_length:
            return {
                "valid": False,
                "error": f"Answer must be at least {min_length} characters"
            }
        
        # Validate maximum length
        max_length = validation.get("max_length")
        if max_length and len(str(answer)) > max_length:
            return {
                "valid": False,
                "error": f"Answer must be no more than {max_length} characters"
            }
        
        # Validate pattern (regex)
        pattern = validation.get("pattern")
        if pattern:
            import re
            if not re.match(pattern, str(answer)):
                return {
                    "valid": False,
                    "error": validation.get("pattern_message", "Answer format is invalid")
                }
        
        return {
            "valid": True,
            "message": "Valid answer"
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


@tool
async def calculate_progress(
    assessment_id: str
) -> dict:
    """
    Calculate assessment completion progress.
    
    Args:
        assessment_id: ID of the assessment
    
    Returns:
        Dictionary with progress statistics
    """
    try:
        db = get_db_service()
        
        # Get assessment
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            return {
                "success": False,
                "error": f"Assessment {assessment_id} not found"
            }
        
        current_answers = assessment.get('answers', {})
        
        decision_tree = get_decision_tree()
        questions = decision_tree.get("questions", [])
        
        # Filter applicable questions based on conditions
        applicable_questions = []
        for question in questions:
            conditions = question.get("conditions", [])
            if not conditions or _evaluate_conditions(conditions, current_answers):
                applicable_questions.append(question)
        
        total_questions = len(applicable_questions)
        answered_questions = len([
            q for q in applicable_questions 
            if q.get("id") in current_answers
        ])
        
        if total_questions == 0:
            percentage = 0
        else:
            percentage = round((answered_questions / total_questions) * 100, 1)
        
        # Calculate progress by risk area
        progress_by_area = {}
        for question in applicable_questions:
            risk_area = question.get("risk_area", "General")
            if risk_area not in progress_by_area:
                progress_by_area[risk_area] = {"total": 0, "answered": 0}
            
            progress_by_area[risk_area]["total"] += 1
            if question.get("id") in current_answers:
                progress_by_area[risk_area]["answered"] += 1
        
        # Calculate percentages per area
        for area, stats in progress_by_area.items():
            stats["percentage"] = round((stats["answered"] / stats["total"]) * 100, 1)
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "completion_percentage": percentage,
            "is_complete": percentage == 100,
            "progress_by_risk_area": progress_by_area,
            "remaining_questions": total_questions - answered_questions
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "completion_percentage": 0
        }


@tool
def get_question_by_id(question_id: str) -> dict:
    """
    Get details of a specific question by ID.
    
    Args:
        question_id: ID of the question to retrieve
    
    Returns:
        Dictionary with question details
    """
    try:
        decision_tree = get_decision_tree()
        questions = decision_tree.get("questions", [])
        
        question = next((q for q in questions if q.get("id") == question_id), None)
        
        if not question:
            return {
                "success": False,
                "error": f"Question {question_id} not found"
            }
        
        return {
            "success": True,
            "question_id": question_id,
            "question": question.get("question", ""),
            "type": question.get("type", "text"),
            "required": question.get("required", True),
            "options": question.get("options", []),
            "help_text": question.get("help_text", ""),
            "risk_area": question.get("risk_area", "General"),
            "validation": question.get("validation", {}),
            "conditions": question.get("conditions", [])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def get_risk_areas(assessment_id: str) -> dict:
    """
    Get all risk areas in an assessment with their completion status.
    
    Args:
        assessment_id: ID of the assessment
    
    Returns:
        Dictionary with risk areas and their status
    """
    try:
        db = get_db_service()
        
        # Get assessment
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            return {
                "success": False,
                "error": f"Assessment {assessment_id} not found"
            }
        
        current_answers = assessment.get('answers', {})
        # Only show risk areas attached to this assessment
        active_risk_areas = assessment.get('active_risk_areas', [])
        decision_tree = get_decision_tree()
        risk_areas_config = decision_tree.get("risk_areas", [])
        questions = decision_tree.get("questions", [])
        # Build risk area status for only attached areas
        risk_area_status = []
        for risk_area in risk_areas_config:
            area_id = risk_area.get("id")
            if area_id not in active_risk_areas:
                continue
            area_questions = [q for q in questions if q.get("risk_area") == area_id]
            answered = len([q for q in area_questions if q.get("id") in current_answers])
            total = len(area_questions)
            percentage = round((answered / total) * 100, 1) if total > 0 else 0
            risk_area_status.append({
                "id": area_id,
                "name": risk_area.get("name"),
                "description": risk_area.get("description"),
                "icon": risk_area.get("icon"),
                "total_questions": total,
                "answered_questions": answered,
                "completion_percentage": percentage,
                "is_complete": percentage == 100
            })
        return {
            "success": True,
            "assessment_id": assessment_id,
            "risk_areas": risk_area_status,
            "total_risk_areas": len(risk_area_status)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
