"""
Assessment Review Tools - For Assessor Workflow
Handles comments, approval/rejection, and review access
"""

from datetime import datetime
from typing import Dict, Any, Optional
import uuid
from strands import tool
import logging

logger = logging.getLogger(__name__)


def get_db_service():
    """Get DynamoDB service instance."""
    from backend.services.dynamodb_service import DynamoDBService
    return DynamoDBService()


@tool
async def add_question_comment(
    assessment_id: str,
    question_id: str,
    comment: str,
    author: str,
    role: str,  # 'requestor' or 'assessor'
    context: dict = None
) -> dict:
    """
    Add a comment to a specific question.

    Args:
        assessment_id: TRA ID
        question_id: Question ID (e.g., 'AI-04')
        comment: Comment text
        author: Name/email of commenter
        role: 'requestor' or 'assessor'
        context: Shared context dictionary

    Returns:
        dict: {success, comment_id, message}
    """
    if context is None:
        context = {}

    try:
        db = get_db_service()

        # Get assessment
        assessment = await db.get_assessment(assessment_id)
        if not assessment:
            return {"success": False, "message": "Assessment not found"}

        # Initialize question_comments if not exists
        if 'question_comments' not in assessment:
            assessment['question_comments'] = {}

        if question_id not in assessment['question_comments']:
            assessment['question_comments'][question_id] = []

        # Create comment object
        comment_id = str(uuid.uuid4())[:8]
        comment_obj = {
            'comment_id': comment_id,
            'author': author,
            'role': role,
            'comment': comment,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Append comment
        assessment['question_comments'][question_id].append(comment_obj)

        # Update in DynamoDB
        await db.update_assessment(
            assessment_id,
            updates={'question_comments': assessment['question_comments']}
        )

        logger.info(f"Added comment {comment_id} to {question_id} by {author} ({role})")

        return {
            "success": True,
            "comment_id": comment_id,
            "message": f"Comment added to {question_id}"
        }

    except Exception as e:
        logger.error(f"Error adding comment: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Error adding comment: {str(e)}"
        }


@tool
async def get_review_data(
    assessment_id: str,
    risk_areas_filter: Optional[str] = None,
    include_comments: bool = True,
    context: dict = None
) -> dict:
    """
    Get review data with Q&A pairs and comments.
    Extends the existing review_answers functionality.

    Args:
        assessment_id: TRA ID
        risk_areas_filter: Optional comma-separated risk area IDs
        include_comments: Whether to include comments
        context: Shared context dictionary

    Returns:
        dict: {qa_pairs, comments, assessment_state, metadata}
    """
    if context is None:
        context = {}

    try:
        # Import here to avoid circular dependency
        from backend.tools.status_tools import review_answers

        # Get Q&A pairs using existing tool (review_answers only takes assessment_id)
        review_result = await review_answers(assessment_id)

        # Get assessment for comments and metadata
        db = get_db_service()
        assessment = await db.get_assessment(assessment_id)

        if not assessment:
            return {"error": "Assessment not found"}

        # Extract qa_pairs from review_data structure
        # review_result has 'review_data' which is a list of risk areas
        # Each risk area has 'qa_pairs', 'risk_area', 'risk_area_id'
        all_qa_pairs = []
        review_data_list = review_result.get('review_data', [])

        for risk_area_data in review_data_list:
            risk_area = risk_area_data.get('risk_area', '')
            risk_area_id = risk_area_data.get('risk_area_id', '')
            qa_pairs = risk_area_data.get('qa_pairs', [])

            # Add risk area info to each qa pair
            for qa in qa_pairs:
                qa['risk_area'] = risk_area
                qa['risk_area_id'] = risk_area_id
                all_qa_pairs.append(qa)

        # Filter by risk areas if specified
        if risk_areas_filter:
            # Parse comma-separated filter (e.g., "ai_risk,ip_risk")
            filter_list = [area.strip().lower().replace(' ', '_') for area in risk_areas_filter.split(',')]

            # Filter qa_pairs to only include those from selected risk areas
            filtered_qa_pairs = []
            for qa in all_qa_pairs:
                risk_area_id = qa.get('risk_area_id', '').lower()
                if risk_area_id in filter_list:
                    filtered_qa_pairs.append(qa)

            all_qa_pairs = filtered_qa_pairs
            logger.info(f"Filtered to {len(all_qa_pairs)} Q&A pairs from risk areas: {filter_list}")

        result = {
            "qa_pairs": all_qa_pairs,
            "assessment_id": assessment_id,
            "project_name": assessment.get('project_name', ''),
            "current_state": assessment.get('current_state', 'draft'),
            "completion_percentage": float(assessment.get('completion_percentage', 0)),
            "requestor_name": assessment.get('requestor_name', ''),
            "requestor_email": assessment.get('requestor_email', ''),
            "submitted_at": assessment.get('submitted_at'),
            "comments": {}
        }

        # Include comments if requested
        if include_comments:
            all_comments = assessment.get('question_comments', {})

            # If filtering by risk areas, only include comments for questions in those risk areas
            if risk_areas_filter:
                # Get list of question IDs from filtered qa_pairs
                question_ids = {qa['question_id'] for qa in all_qa_pairs}

                # Filter comments to only include those for filtered questions
                filtered_comments = {
                    q_id: comments
                    for q_id, comments in all_comments.items()
                    if q_id in question_ids
                }
                result["comments"] = filtered_comments
            else:
                result["comments"] = all_comments

        logger.info(f"Retrieved review data for {assessment_id}: {len(result['qa_pairs'])} Q&A pairs, {len(result['comments'])} questions with comments")

        return result

    except Exception as e:
        logger.error(f"Error fetching review data: {e}", exc_info=True)
        return {"error": f"Error fetching review data: {str(e)}"}


@tool
async def submit_for_review(
    assessment_id: str,
    context: dict = None
) -> dict:
    """
    Submit assessment for review with per-risk-area assessor links.
    Only generates links for COMPLETED risk areas (100% answered).
    Changes state to SUBMITTED if any risk area is complete.

    Args:
        assessment_id: TRA ID
        context: Shared context dictionary

    Returns:
        dict: {success, submitted_risk_areas, incomplete_risk_areas, message}
    """
    if context is None:
        context = {}

    try:
        import uuid
        from backend.tools.status_tools import update_state
        from backend.core.config import get_settings

        settings = get_settings()

        # 1. Get review data to analyze risk areas
        review_result = await get_review_data(assessment_id, risk_areas_filter=None, include_comments=False, context=context)

        if not review_result or 'qa_pairs' not in review_result:
            return {
                "success": False,
                "message": "Could not retrieve assessment data for submission."
            }

        # 2. Group Q&A by risk area and calculate completion
        risk_area_stats = {}
        for qa in review_result['qa_pairs']:
            risk_area = qa.get('risk_area', 'Unknown')
            risk_area_id = qa.get('risk_area_id', 'unknown')

            if risk_area_id not in risk_area_stats:
                risk_area_stats[risk_area_id] = {
                    'risk_area': risk_area,
                    'risk_area_id': risk_area_id,
                    'total_questions': 0,
                    'questions_answered': 0
                }

            risk_area_stats[risk_area_id]['total_questions'] += 1
            answer = qa.get('answer', '')
            if answer and answer.strip() and answer != 'Not answered':
                risk_area_stats[risk_area_id]['questions_answered'] += 1

        # 3. Generate links for COMPLETE risk areas only
        submitted_risk_areas = []
        incomplete_risk_areas = []

        for risk_area_id, stats in risk_area_stats.items():
            completion = (stats['questions_answered'] / stats['total_questions'] * 100) if stats['total_questions'] > 0 else 0
            stats['completion'] = round(completion, 1)

            if stats['questions_answered'] == stats['total_questions']:
                # Generate unique token for this risk area
                token = str(uuid.uuid4())

                # Create filtered assessor link using review.html
                # Format: http://localhost:8000/review.html?tra=TRA-X&mode=assessor&risk_areas=intellectual_property&token=abc
                base_url = settings.assessor_base_url.rstrip('/assess')  # Remove /assess if present
                assessor_link = f"{base_url}/review.html?tra={assessment_id}&mode=assessor&risk_areas={risk_area_id}&token={token}"

                stats['assessor_link'] = assessor_link
                stats['token'] = token
                stats['status'] = 'submitted'
                submitted_risk_areas.append(stats)

                logger.info(f"Generated assessor link for {risk_area} ({risk_area_id}): {assessor_link}")
            else:
                stats['status'] = 'incomplete'
                incomplete_risk_areas.append(stats)
                logger.info(f"Risk area {risk_area} ({risk_area_id}) incomplete: {stats['questions_answered']}/{stats['total_questions']}")

        # 4. Update assessment state to SUBMITTED if any risk area is complete
        if submitted_risk_areas:
            await update_state(assessment_id, 'submitted')
            logger.info(f"Assessment {assessment_id} state changed to SUBMITTED")

        # 5. Format response message
        message_parts = []

        if submitted_risk_areas:
            message_parts.append(f"✅ Assessment submitted for review!\n")
            message_parts.append(f"📊 **Risk Area Status:**\n")

            for stats in submitted_risk_areas:
                message_parts.append(f"\n✅ **{stats['risk_area']} - Ready for Review**")
                message_parts.append(f"   - {stats['questions_answered']}/{stats['total_questions']} questions answered ({stats['completion']}%)")
                message_parts.append(f"   - **Assessor Link:** {stats['assessor_link']}")

        if incomplete_risk_areas:
            if submitted_risk_areas:
                message_parts.append(f"\n")

            for stats in incomplete_risk_areas:
                message_parts.append(f"\n⚠️  **{stats['risk_area']} - Incomplete**")
                message_parts.append(f"   - {stats['questions_answered']}/{stats['total_questions']} questions answered ({stats['completion']}%)")
                message_parts.append(f"   - Complete remaining questions before submitting")

        if submitted_risk_areas:
            message_parts.append(f"\n\n💡 **Next Steps:**")
            message_parts.append(f"   - Share the assessor links with your Assessment Group reviewers")
            message_parts.append(f"   - Each link is filtered to show only the relevant risk area questions")

        message = "\n".join(message_parts)

        return {
            "success": True,
            "assessment_id": assessment_id,
            "submitted_risk_areas": submitted_risk_areas,
            "incomplete_risk_areas": incomplete_risk_areas,
            "total_submitted": len(submitted_risk_areas),
            "total_incomplete": len(incomplete_risk_areas),
            "message": message
        }

    except Exception as e:
        logger.error(f"Error submitting for review: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Error submitting for review: {str(e)}"
        }


@tool
async def assessor_decision(
    assessment_id: str,
    decision: str,  # 'approve' or 'reject'
    overall_comment: Optional[str] = None,
    assessor_name: Optional[str] = None,
    context: dict = None
) -> dict:
    """
    Assessor approves or rejects the assessment.

    Args:
        assessment_id: TRA ID
        decision: 'approve' or 'reject'
        overall_comment: Optional overall feedback
        assessor_name: Name of assessor
        context: Shared context dictionary

    Returns:
        dict: {success, new_state, message}
    """
    if context is None:
        context = {}

    try:
        from backend.tools.status_tools import update_state
        from backend.models.tra_models import AssessmentState

        db = get_db_service()

        # Validate decision
        if decision not in ['approve', 'reject']:
            return {"success": False, "message": "Decision must be 'approve' or 'reject'"}

        # Get current state
        assessment = await db.get_assessment(assessment_id)
        if not assessment:
            return {"success": False, "message": "Assessment not found"}

        current_state = assessment.get('current_state', 'draft')

        # Determine new state
        if decision == 'approve':
            new_state = AssessmentState.FINALIZED
            message = "Assessment approved and finalized"
        else:
            new_state = AssessmentState.SENT_BACK
            message = "Assessment sent back for revisions"

        # Update state using the update_state tool
        await update_state(
            assessment_id=assessment_id,
            new_state=new_state.value
        )

        # Add overall comment if provided
        if overall_comment:
            updates = {'assessor_feedback': overall_comment}
            if assessor_name:
                updates['assigned_assessor'] = assessor_name

            await db.update_assessment(assessment_id, updates=updates)

        logger.info(f"Assessment {assessment_id} {decision}ed by {assessor_name or 'Unknown'}")

        return {
            "success": True,
            "new_state": new_state.value,
            "message": message,
            "assessment_id": assessment_id
        }

    except Exception as e:
        logger.error(f"Error processing decision: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Error processing decision: {str(e)}"
        }
