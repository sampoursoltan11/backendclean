"""
Pydantic models for TRA system - Simplified version
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import TYPE_CHECKING


class AssessmentState(str, Enum):
    """Assessment workflow states."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    SENT_BACK = "sent_back"
    FINALIZED = "finalized"


class EventType(str, Enum):
    """Event types for audit trail."""
    ASSESSMENT_CREATED = "assessment_created"
    QUESTION_ANSWERED = "question_answered"
    QUESTION_MODIFIED = "question_modified"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_PROCESSED = "document_processed"
    RAG_SUGGESTION_GENERATED = "rag_suggestion_generated"
    RAG_SUGGESTION_ACCEPTED = "rag_suggestion_accepted"
    RAG_SUGGESTION_REJECTED = "rag_suggestion_rejected"
    RAG_SUGGESTION_MODIFIED = "rag_suggestion_modified"
    ASSESSMENT_SUBMITTED = "assessment_submitted"
    REVIEW_STARTED = "review_started"
    REVIEW_SAVED = "review_saved"
    ASSESSMENT_SENT_BACK = "assessment_sent_back"
    ASSESSMENT_FINALIZED = "assessment_finalized"
    EXPORT_GENERATED = "export_generated"
    VERSION_CREATED = "version_created"
    STATUS_CHECKED = "status_checked"


class UserRole(str, Enum):
    """User roles in the system."""
    REQUESTOR = "requestor"
    ASSESSOR = "assessor"
    STAKEHOLDER = "stakeholder"
    ADMIN = "admin"


class RiskAreaStatus(str, Enum):
    """Status for individual risk area segments."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class TRAComplexity(str, Enum):
    """TRA complexity levels for effort estimation."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


class BaseEntity(BaseModel):
    """Base entity with common fields."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TraAssessment(BaseEntity):
    """
    Technology Risk Assessment model.
    
    Note: assessment_id IS the TRA ID - they are the same identifier.
    Format: TRA-2025-{6_HEX} (e.g., TRA-2025-A1B2C3)
    This is the single source of truth for all assessment operations.
    """
    
    # Primary identifiers
    assessment_id: str = Field(..., description="Unique assessment identifier (TRA ID format: TRA-2025-XXXXXX)")
    session_id: str = Field(default_factory=lambda: "local", description="WebSocket session identifier")
    
    # Assessment metadata
    title: Optional[str] = Field(None, description="Assessment title")
    description: Optional[str] = Field(None, description="Assessment description")
    technology_type: Optional[str] = Field(None, description="Type of technology being assessed")
    
    # NEW: Project metadata for better tracking
    system_id: Optional[str] = Field(None, description="System/Project ID for tracking")
    classification: Optional[str] = Field(None, description="Data classification (e.g., Confidential, Public)")
    business_unit: Optional[str] = Field(None, description="Business unit or department")
    
    # Requestor information
    requestor_name: Optional[str] = Field(None, description="Name of person requesting assessment")
    requestor_email: Optional[str] = Field(None, description="Email of requestor")
    
    # Assessment data
    answers: Dict[str, Any] = Field(default_factory=dict, description="Question-answer pairs")
    completion_percentage: float = Field(default=0.0, description="Assessment completion percentage")
    current_question_id: Optional[str] = Field(None, description="Current active question ID for state tracking")
    
    # NEW: Risk area tracking
    active_risk_areas: List[str] = Field(default_factory=list, description="Active risk areas being assessed")
    
    # NEW: Document linking
    linked_documents: List[Dict[str, Any]] = Field(default_factory=list, description="Documents linked to this assessment")
    
    # Workflow state
    current_state: AssessmentState = Field(default=AssessmentState.DRAFT, description="Current workflow state")
    
    # Versioning
    version: int = Field(default=1, description="Version number")
    parent_assessment_id: Optional[str] = Field(None, description="Parent assessment ID for versions")
    
    # Assessor information
    assigned_assessor: Optional[str] = Field(None, description="Assigned assessor identifier")
    assessor_link: Optional[str] = Field(None, description="Static link for assessor access")
    
    # Timestamps
    submitted_at: Optional[datetime] = Field(None, description="Submission timestamp")
    finalized_at: Optional[datetime] = Field(None, description="Finalization timestamp")
    
    # DynamoDB keys
    pk: Optional[str] = Field(None, description="DynamoDB partition key")
    sk: Optional[str] = Field(None, description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")
    gsi2_pk: Optional[str] = Field(None, description="GSI2 partition key")
    gsi2_sk: Optional[str] = Field(None, description="GSI2 sort key")

    def model_post_init(self, __context: Any) -> None:  # type: ignore[override]
        # Auto-populate DynamoDB keys if missing for compatibility with simplified tests
        try:
            if not self.pk:
                self.pk = f"ASSESSMENT#{self.assessment_id}"
            if not self.sk:
                # Use created_at from BaseEntity; ensure it's a datetime
                created = self.created_at if isinstance(self.created_at, datetime) else datetime.utcnow()
                self.sk = f"METADATA#{created.isoformat()}"
        except Exception:
            # Be defensive; do not break validation if fields are unexpectedly missing
            if not self.pk and getattr(self, 'assessment_id', None):
                self.pk = f"ASSESSMENT#{getattr(self, 'assessment_id')}"
            if not self.sk:
                self.sk = f"METADATA#{datetime.utcnow().isoformat()}"


class TraEvent(BaseEntity):
    """Event model for audit trail."""
    
    # Event identifiers
    event_id: str = Field(..., description="Unique event identifier")
    assessment_id: str = Field(..., description="Related assessment ID")
    session_id: Optional[str] = Field(None, description="Session where event occurred")
    
    # Event details
    event_type: EventType = Field(..., description="Type of event")
    description: str = Field(..., description="Human-readable event description")
    actor: Optional[str] = Field(None, description="Who performed the action")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    
    # DynamoDB keys
    pk: str = Field(..., description="DynamoDB partition key")
    sk: str = Field(..., description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")
    gsi2_pk: Optional[str] = Field(None, description="GSI2 partition key")
    gsi2_sk: Optional[str] = Field(None, description="GSI2 sort key")


class ChatMessage(BaseEntity):
    """Chat message model for real-time conversation."""
    
    # Message identifiers
    message_id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Chat session identifier")
    assessment_id: Optional[str] = Field(None, description="Related assessment ID")
    
    # Message content
    message_type: str = Field(..., description="Type of message")
    role: str = Field(..., description="Message sender role")
    content: str = Field(..., description="Message content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Message-specific data")
    
    # Processing status
    processed: bool = Field(default=False, description="Whether message was processed")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    
    # DynamoDB keys
    pk: str = Field(..., description="DynamoDB partition key")
    sk: str = Field(..., description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")


class DocumentMetadata(BaseEntity):
    """Document metadata model with enhanced tracking."""
    
    # Document identifiers
    document_id: str = Field(..., description="Unique document identifier")
    session_id: str = Field(..., description="Session where document was uploaded")
    assessment_id: Optional[str] = Field(None, description="Related assessment ID")
    
    # File information
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    
    # Storage information
    s3_key: str = Field(..., description="S3 object key")
    s3_bucket: Optional[str] = Field(None, description="S3 bucket name")
    
    # Enhanced metadata fields
    project_name: Optional[str] = Field(None, description="Associated project name")
    file_category: str = Field(default="document", description="File category (document, spreadsheet, presentation)")
    content_summary: str = Field(default="", description="Brief description of file content")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    upload_context: Dict[str, Any] = Field(default_factory=dict, description="Upload context metadata")
    
    # Processing status
    processing_status: str = Field(default="uploaded", description="Document processing state")
    chunk_count: Optional[int] = Field(None, description="Number of text chunks created")
    embedding_model: Optional[str] = Field(None, description="Model used for embeddings")
    kb_indexed: bool = Field(default=False, description="Whether indexed in Knowledge Base")
    error_message: Optional[str] = Field(None, description="Error details if processing failed")
    
    # Processing timestamps
    processed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    
    # DynamoDB keys
    pk: str = Field(..., description="DynamoDB partition key")
    sk: str = Field(..., description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")
    gsi2_pk: Optional[str] = Field(None, description="GSI2 partition key")
    gsi2_sk: Optional[str] = Field(None, description="GSI2 sort key")


class AssessmentReview(BaseEntity):
    """Assessment review model."""
    
    # Review identifiers
    review_id: str = Field(..., description="Unique review identifier")
    assessment_id: str = Field(..., description="Assessment being reviewed")
    
    # Assessor information
    assessor_id: str = Field(..., description="Assessor identifier")
    assessor_name: Optional[str] = Field(None, description="Assessor name")
    
    # Review status
    review_status: str = Field(default="draft", description="Current review status")
    
    # Review content
    overall_comment: Optional[str] = Field(None, description="General assessment feedback")
    risk_rating: Optional[int] = Field(None, description="Risk score (1-5 scale)")
    completeness_rating: Optional[int] = Field(None, description="Completeness score (1-5 scale)")
    recommended_controls: List[str] = Field(default_factory=list, description="Recommended security controls")
    send_back_comment: Optional[str] = Field(None, description="Feedback for send-back scenarios")
    question_feedback: Dict[str, str] = Field(default_factory=dict, description="Specific feedback per question")
    
    # Review timestamps
    submitted_at: Optional[datetime] = Field(None, description="Review submission timestamp")
    
    # DynamoDB keys
    pk: str = Field(..., description="DynamoDB partition key")
    sk: str = Field(..., description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")
    gsi2_pk: Optional[str] = Field(None, description="GSI2 partition key")
    gsi2_sk: Optional[str] = Field(None, description="GSI2 sort key")


class ExportRecord(BaseEntity):
    """Export record model."""
    
    # Export identifiers
    export_id: str = Field(..., description="Unique export identifier")
    assessment_id: str = Field(..., description="Source assessment")
    
    # Export details
    export_type: str = Field(..., description="Type of export (docx, json, pdf)")
    export_status: str = Field(default="requested", description="Generation status")
    
    # File information
    s3_key: Optional[str] = Field(None, description="S3 location of generated file")
    s3_bucket: Optional[str] = Field(None, description="S3 bucket name")
    file_size: Optional[int] = Field(None, description="Generated file size in bytes")
    download_url: Optional[str] = Field(None, description="Pre-signed download URL")
    url_expires_at: Optional[datetime] = Field(None, description="Download URL expiration")
    
    # Request information
    requested_by: str = Field(..., description="Who requested the export")
    error_message: Optional[str] = Field(None, description="Error details if generation failed")
    
    # Processing timestamps
    completed_at: Optional[datetime] = Field(None, description="Export completion timestamp")
    
    # DynamoDB keys
    pk: str = Field(..., description="DynamoDB partition key")
    sk: str = Field(..., description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")
    gsi2_pk: Optional[str] = Field(None, description="GSI2 partition key")
    gsi2_sk: Optional[str] = Field(None, description="GSI2 sort key")


class UserProfile(BaseEntity):
    """User profile model."""
    
    # User identifiers
    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    
    # User information
    name: Optional[str] = Field(None, description="User full name")
    role: UserRole = Field(..., description="User role in system")
    department: Optional[str] = Field(None, description="User department")
    
    # User preferences
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    
    # Status
    is_active: bool = Field(default=True, description="Whether user is active")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    # DynamoDB keys
    pk: str = Field(..., description="DynamoDB partition key")
    sk: str = Field(..., description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")


# Enhanced TRA_DATA Table Integration Models

class RiskAreaSegment(BaseModel):
    """Individual risk area segment within a TRA."""
    
    segment_id: str = Field(..., description="Unique segment identifier")
    risk_area: str = Field(..., description="Risk area name (e.g., Data Security)")
    status: RiskAreaStatus = Field(default=RiskAreaStatus.NOT_STARTED, description="Segment status")
    
    # Progress tracking
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage")
    questions_answered: int = Field(default=0, description="Number of questions answered")
    total_questions: int = Field(default=0, description="Total questions in this risk area")
    
    # Content and documentation
    questions: List[Dict[str, Any]] = Field(default_factory=list, description="Questions for this risk area")
    answers: Dict[str, Any] = Field(default_factory=dict, description="Answers provided")
    documents: List[str] = Field(default_factory=list, description="Associated document IDs")
    
    # Metadata
    priority_level: str = Field(default="medium", description="Priority level (low/medium/high/critical)")
    estimated_effort_hours: Optional[float] = Field(None, description="Estimated effort in hours")
    actual_effort_hours: Optional[float] = Field(None, description="Actual time spent")
    
    # Timestamps
    started_at: Optional[datetime] = Field(None, description="When work started on this segment")
    completed_at: Optional[datetime] = Field(None, description="When segment was completed")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    
    # Assignment
    assigned_to: Optional[str] = Field(None, description="Who is working on this segment")
    reviewer: Optional[str] = Field(None, description="Who reviews this segment")
    
    # Quality metrics
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality assessment score")
    review_notes: Optional[str] = Field(None, description="Review feedback")


class EnhancedTRAAssessment(BaseEntity):
    """
    Enhanced TRA Assessment leveraging TRA_DATA table structure.
    
    DEPRECATED/UNUSED: This model is not currently used in the production system.
    The actual system uses TraAssessment with assessment_id as the primary identifier.
    This model was designed for future enhancements but has not been integrated.
    
    Note: tra_id in this model is intended to be the same as assessment_id in TraAssessment.
    For backward compatibility, assessment_id field is included below.
    """
    
    # Core TRA metadata (from TRA_DATA structure)
    tra_id: str = Field(..., description="TRA identifier (e.g., TRA-2025-001) - SAME AS assessment_id")
    title: str = Field(..., description="Assessment title")
    description: Optional[str] = Field(None, description="Detailed assessment description")
    
    # Project and organizational context
    project_id: str = Field(..., description="Associated project identifier")
    project_name: Optional[str] = Field(None, description="Human-readable project name")
    business_unit: str = Field(..., description="Business unit or department")
    cost_center: Optional[str] = Field(None, description="Cost center for tracking")
    
    # Assessment metadata
    assessment_type: str = Field(default="technology_risk", description="Type of assessment")
    complexity_level: TRAComplexity = Field(default=TRAComplexity.MODERATE, description="Assessment complexity")
    compliance_frameworks: List[str] = Field(default_factory=list, description="Applicable compliance frameworks")
    
    # Creator and ownership
    creator_info: str = Field(..., description="Creator name and contact")
    creator_role: str = Field(..., description="Creator's role/title")
    business_owner: Optional[str] = Field(None, description="Business owner for the assessment")
    technical_owner: Optional[str] = Field(None, description="Technical owner/lead")
    
    # Risk area segments (core TRA_DATA feature)
    risk_segments: List[RiskAreaSegment] = Field(
        default_factory=list, 
        description="Risk area segments with individual tracking"
    )
    
    # Progress and completion tracking
    overall_status: AssessmentState = Field(default=AssessmentState.DRAFT, description="Overall TRA status")
    completion_matrix: Dict[str, float] = Field(
        default_factory=dict, 
        description="Completion percentage per risk area"
    )
    overall_completion: float = Field(default=0.0, ge=0.0, le=100.0, description="Overall completion percentage")
    
    # Timeline and effort
    target_completion_date: Optional[datetime] = Field(None, description="Target completion date")
    estimated_effort_hours: Optional[float] = Field(None, description="Total estimated effort")
    actual_effort_hours: Optional[float] = Field(None, description="Actual time spent")
    
    # Quality and review
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall quality score")
    review_status: str = Field(default="pending", description="Review status")
    risk_rating: Optional[str] = Field(None, description="Overall risk rating")
    
    # Integration with current system
    session_id: Optional[str] = Field(None, description="Associated chat session")
    assessment_id: str = Field(..., description="Current system assessment ID for backward compatibility")
    
    # Enhanced tracking
    version: int = Field(default=1, description="Assessment version")
    parent_tra_id: Optional[str] = Field(None, description="Parent TRA if this is a revision")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    
    # Automation and AI features
    auto_suggestions_enabled: bool = Field(default=True, description="Enable AI suggestions")
    document_analysis_complete: bool = Field(default=False, description="Document analysis status")
    smart_routing_enabled: bool = Field(default=True, description="Enable smart question routing")
    
    # DynamoDB keys (enhanced for TRA_DATA integration)
    pk: str = Field(..., description="DynamoDB partition key")
    sk: str = Field(..., description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key for project queries")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")
    gsi2_pk: Optional[str] = Field(None, description="GSI2 partition key for business unit queries")
    gsi2_sk: Optional[str] = Field(None, description="GSI2 sort key")
    
    def get_risk_area_status(self, risk_area: str) -> Optional[RiskAreaSegment]:
        """Get status of a specific risk area."""
        for segment in self.risk_segments:
            if segment.risk_area == risk_area:
                return segment
        return None
    
    def calculate_overall_completion(self) -> float:
        """Calculate overall completion based on risk area segments."""
        if not self.risk_segments:
            return 0.0
        
        total_completion = sum(segment.completion_percentage for segment in self.risk_segments)
        return total_completion / len(self.risk_segments)
    
    def get_next_priority_area(self) -> Optional[str]:
        """Get the next priority risk area to work on."""
        # Find incomplete areas, prioritized by priority level and current progress
        incomplete_areas = [
            segment for segment in self.risk_segments 
            if segment.status != RiskAreaStatus.COMPLETED
        ]
        
        if not incomplete_areas:
            return None
        
        # Sort by priority and progress
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        
        sorted_areas = sorted(
            incomplete_areas,
            key=lambda x: (
                priority_order.get(x.priority_level, 4),
                -x.completion_percentage  # Prefer areas with some progress
            )
        )
        
        return sorted_areas[0].risk_area if sorted_areas else None


# Response models for API
class AssessmentResponse(BaseModel):
    """API response model for assessments."""
    assessment_id: str
    title: Optional[str]
    current_state: AssessmentState
    completion_percentage: float
    created_at: datetime
    updated_at: datetime
    assessor_link: Optional[str] = None


class StatusResponse(BaseModel):
    """API response model for status checks."""
    assessment_id: str
    current_state: AssessmentState
    status_message: str
    last_updated: datetime
    next_action: Optional[str] = None
    assessor_feedback: Optional[str] = None


class ChatResponse(BaseModel):
    """API response model for chat interactions."""
    message_id: str
    response: str
    next_action: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)


class HealthCheckResponse(BaseModel):
    """API response model for health checks."""
    success: bool
    system: str
    timestamp: datetime
    services: Dict[str, Any]


# Enhanced Agent Performance Models

class AgentDecisionType(str, Enum):
    """Types of agent decisions."""
    INTENT_CLASSIFICATION = "intent_classification"
    QUESTION_ROUTING = "question_routing"
    RAG_RETRIEVAL = "rag_retrieval"
    ANSWER_GENERATION = "answer_generation"
    DOCUMENT_ANALYSIS = "document_analysis"
    WORKFLOW_ROUTING = "workflow_routing"
    CLARIFICATION_REQUEST = "clarification_request"
    ESCALATION = "escalation"
    ASSESSMENT_CREATION = "assessment_creation"
    QUESTION_PROCESSING = "question_processing"
    ERROR_HANDLING = "error_handling"


class AgentPerformanceMetric(str, Enum):
    """Agent performance metrics."""
    RESPONSE_TIME = "response_time"
    INTENT_ACCURACY = "intent_accuracy"
    RAG_RELEVANCE = "rag_relevance"
    USER_SATISFACTION = "user_satisfaction"
    TASK_COMPLETION = "task_completion"
    ERROR_RATE = "error_rate"
    CONTEXT_RETENTION = "context_retention"
    DECISION_CONFIDENCE = "decision_confidence"


class ConversationPhase(str, Enum):
    """Phases of conversation."""
    INITIATION = "initiation"
    INFORMATION_GATHERING = "information_gathering"
    DOCUMENT_PROCESSING = "document_processing"
    ASSESSMENT_BUILDING = "assessment_building"
    CLARIFICATION = "clarification"
    REVIEW_PREPARATION = "review_preparation"
    COMPLETION = "completion"


class AgentDecision(BaseEntity):
    """Individual agent decision tracking for performance analysis."""
    
    # Decision identifiers
    decision_id: str = Field(..., description="Unique decision identifier")
    session_id: str = Field(..., description="Session where decision was made")
    assessment_id: Optional[str] = Field(None, description="Related assessment ID")
    agent_name: str = Field(..., description="Name of the agent making decision")
    
    # Decision details
    decision_type: AgentDecisionType = Field(..., description="Type of decision made")
    input_context: Dict[str, Any] = Field(default_factory=dict, description="Input context for decision")
    decision_output: Dict[str, Any] = Field(default_factory=dict, description="Agent's decision output")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Agent's confidence in decision")
    
    # Performance metrics
    processing_time_ms: int = Field(..., description="Time taken to make decision in milliseconds")
    tokens_used: Optional[int] = Field(None, description="Number of tokens consumed")
    cost_estimate: Optional[float] = Field(None, description="Estimated cost of operation")
    
    # Context and reasoning
    reasoning: Optional[str] = Field(None, description="Agent's reasoning for the decision")
    alternative_options: List[Dict[str, Any]] = Field(default_factory=list, description="Other options considered")
    decision_path: List[str] = Field(default_factory=list, description="Decision tree path taken")
    
    # Outcome tracking
    user_feedback: Optional[str] = Field(None, description="User feedback on decision outcome")
    success_indicator: Optional[bool] = Field(None, description="Whether decision led to successful outcome")
    correction_needed: bool = Field(default=False, description="Whether decision required correction")
    
    # DynamoDB keys
    pk: str = Field(..., description="DynamoDB partition key")
    sk: str = Field(..., description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")


class ConversationContext(BaseEntity):
    """Enhanced conversation context for better agent performance."""
    
    # Context identifiers
    context_id: str = Field(..., description="Unique context identifier")
    session_id: str = Field(..., description="Associated session")
    assessment_id: Optional[str] = Field(None, description="Related assessment ID")
    
    # Conversation state
    current_phase: ConversationPhase = Field(..., description="Current conversation phase")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history summary")
    active_topics: List[str] = Field(default_factory=list, description="Currently active discussion topics")
    resolved_topics: List[str] = Field(default_factory=list, description="Previously resolved topics")
    
    # User profile and preferences
    user_expertise_level: str = Field(default="intermediate", description="User's technical expertise level")
    communication_style: str = Field(default="standard", description="Preferred communication style")
    preferred_detail_level: str = Field(default="medium", description="User's preferred level of detail")
    
    # Context memory
    key_entities: Dict[str, Any] = Field(default_factory=dict, description="Important entities mentioned")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="Learned user preferences")
    session_goals: List[str] = Field(default_factory=list, description="Session objectives")
    outstanding_questions: List[str] = Field(default_factory=list, description="Questions awaiting answers")
    
    # Document context
    referenced_documents: List[str] = Field(default_factory=list, description="Documents referenced in conversation")
    document_insights: Dict[str, Any] = Field(default_factory=dict, description="Insights derived from documents")
    
    # Performance context
    response_patterns: Dict[str, Any] = Field(default_factory=dict, description="User response patterns")
    successful_strategies: List[str] = Field(default_factory=list, description="Strategies that worked well")
    avoided_patterns: List[str] = Field(default_factory=list, description="Patterns to avoid")
    
    # DynamoDB keys
    pk: str = Field(..., description="DynamoDB partition key")
    sk: str = Field(..., description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")


class AgentPerformanceMetrics(BaseEntity):
    """Aggregate performance metrics for agents."""
    
    # Metrics identifiers
    metrics_id: str = Field(..., description="Unique metrics record identifier")
    agent_name: str = Field(..., description="Agent being measured")
    time_window: str = Field(..., description="Time window for metrics (daily, weekly, monthly)")
    period_start: datetime = Field(..., description="Start of measurement period")
    period_end: datetime = Field(..., description="End of measurement period")
    
    # Performance statistics
    total_decisions: int = Field(default=0, description="Total decisions made in period")
    successful_decisions: int = Field(default=0, description="Successful decisions")
    average_response_time: float = Field(default=0.0, description="Average response time in milliseconds")
    average_confidence: float = Field(default=0.0, description="Average confidence score")
    
    # Detailed metrics
    metrics_by_type: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Metrics broken down by decision type")
    error_analysis: Dict[str, Any] = Field(default_factory=dict, description="Error patterns and causes")
    improvement_suggestions: List[str] = Field(default_factory=list, description="Automated improvement suggestions")
    
    # Resource utilization
    total_tokens_used: int = Field(default=0, description="Total tokens consumed")
    total_cost: float = Field(default=0.0, description="Total cost incurred")
    efficiency_score: float = Field(default=0.0, description="Efficiency score (success/cost ratio)")
    
    # DynamoDB keys
    pk: str = Field(..., description="DynamoDB partition key")
    sk: str = Field(..., description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")

# --- Compatibility export for Variant B tests ---
# The Enhanced orchestrator defines TRASharedState locally. Tests import it from
# backend.models.tra_models. To keep both variants working without large refactors,
# we import and re-export the class here at import time.
class TRASharedState(BaseModel):  # type: ignore
    session_id: str
    user_id: Optional[str] = None
    current_assessment_id: Optional[str] = None
    # Reuse ConversationPhase from this module to keep types consistent
    conversation_phase: ConversationPhase = ConversationPhase.INITIATION
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    context_metadata: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)


class RAGRetrievalRecord(BaseEntity):
    """Enhanced RAG retrieval tracking for optimization."""
    
    # Retrieval identifiers
    retrieval_id: str = Field(..., description="Unique retrieval identifier")
    session_id: str = Field(..., description="Session where retrieval occurred")
    assessment_id: Optional[str] = Field(None, description="Related assessment ID")
    
    # Query details
    query_text: str = Field(..., description="Original query text")
    query_intent: str = Field(..., description="Identified query intent")
    query_complexity: str = Field(default="medium", description="Query complexity level")
    
    # Retrieval configuration
    knowledge_base_id: str = Field(..., description="Knowledge base used")
    retrieval_method: str = Field(..., description="Retrieval method used")
    max_results: int = Field(default=10, description="Maximum results requested")
    similarity_threshold: float = Field(default=0.7, description="Similarity threshold used")
    
    # Results analysis
    results_count: int = Field(..., description="Number of results returned")
    avg_similarity_score: float = Field(..., description="Average similarity score of results")
    result_sources: List[str] = Field(default_factory=list, description="Source documents of results")
    result_diversity: float = Field(default=0.0, description="Diversity score of results")
    
    # Performance metrics
    retrieval_time_ms: int = Field(..., description="Time taken for retrieval")
    relevance_score: Optional[float] = Field(None, description="Human-assessed relevance score")
    user_satisfaction: Optional[int] = Field(None, description="User satisfaction rating (1-5)")
    
    # Post-processing
    used_in_response: bool = Field(default=False, description="Whether results were used in agent response")
    response_quality: Optional[float] = Field(None, description="Quality of generated response")
    follow_up_needed: bool = Field(default=False, description="Whether follow-up queries were needed")
    
    # DynamoDB keys
    pk: str = Field(..., description="DynamoDB partition key")
    sk: str = Field(..., description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")


class DecisionTreeAnalytics(BaseEntity):
    """Decision tree path analysis for optimization."""
    
    # Analytics identifiers
    analytics_id: str = Field(..., description="Unique analytics record identifier")
    session_id: str = Field(..., description="Associated session")
    assessment_id: Optional[str] = Field(None, description="Related assessment ID")
    
    # Path tracking
    decision_path: List[str] = Field(default_factory=list, description="Sequence of decisions made")
    path_efficiency_score: float = Field(default=0.0, description="Efficiency score for the path taken")
    alternative_paths: List[List[str]] = Field(default_factory=list, description="Alternative paths that could have been taken")
    optimal_path: Optional[List[str]] = Field(None, description="Identified optimal path")
    
    # Timing analysis
    total_path_time: int = Field(default=0, description="Total time for complete path in milliseconds")
    step_timings: List[int] = Field(default_factory=list, description="Time for each step in path")
    bottleneck_steps: List[str] = Field(default_factory=list, description="Steps identified as bottlenecks")
    
    # Outcome analysis
    path_success: bool = Field(default=False, description="Whether path led to successful outcome")
    user_satisfaction: Optional[int] = Field(None, description="User satisfaction with path (1-5)")
    completion_rate: float = Field(default=0.0, description="Percentage of path completed")
    
    # Learning insights
    effective_patterns: List[str] = Field(default_factory=list, description="Effective decision patterns identified")
    improvement_opportunities: List[str] = Field(default_factory=list, description="Areas for improvement")
    recommended_optimizations: List[str] = Field(default_factory=list, description="Recommended path optimizations")
    
    # DynamoDB keys
    pk: str = Field(..., description="DynamoDB partition key")
    sk: str = Field(..., description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")


class AgentLearningRecord(BaseEntity):
    """Agent learning and adaptation tracking."""
    
    # Learning identifiers
    learning_id: str = Field(..., description="Unique learning record identifier")
    agent_name: str = Field(..., description="Agent that learned")
    learning_trigger: str = Field(..., description="What triggered the learning")
    
    # Learning content
    learning_type: str = Field(..., description="Type of learning (pattern, preference, correction)")
    learned_pattern: Dict[str, Any] = Field(default_factory=dict, description="Pattern or rule learned")
    context_conditions: List[str] = Field(default_factory=list, description="Conditions when pattern applies")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence in learned pattern")
    
    # Validation
    validation_attempts: int = Field(default=0, description="Number of times pattern was tested")
    success_rate: float = Field(default=0.0, description="Success rate of pattern application")
    last_validation: Optional[datetime] = Field(None, description="Last time pattern was validated")
    
    # Application tracking
    times_applied: int = Field(default=0, description="Number of times pattern was applied")
    effectiveness_score: float = Field(default=0.0, description="Overall effectiveness score")
    
    # DynamoDB keys
    pk: str = Field(..., description="DynamoDB partition key")
    sk: str = Field(..., description="DynamoDB sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")


# Enhanced API Response Models

class AgentPerformanceResponse(BaseModel):
    """API response model for agent performance metrics."""
    agent_name: str
    time_period: str
    total_decisions: int
    success_rate: float
    average_response_time: float
    average_confidence: float
    efficiency_score: float
    improvement_areas: List[str]
    top_patterns: List[Dict[str, Any]]


class ConversationInsightsResponse(BaseModel):
    """API response model for conversation insights."""
    session_id: str
    current_phase: ConversationPhase
    progress_score: float
    key_topics: List[str]
    user_engagement: float
    recommended_actions: List[str]
    context_quality: float


class RAGPerformanceResponse(BaseModel):
    """API response model for RAG performance analytics."""
    time_period: str
    total_retrievals: int
    average_relevance: float
    average_response_time: float
    top_performing_queries: List[str]
    improvement_suggestions: List[str]
    knowledge_gap_indicators: List[str]


class DecisionAnalyticsResponse(BaseModel):
    """API response model for decision tree analytics."""
    session_id: str
    decision_path: List[str]
    path_efficiency: float
    optimal_alternative: Optional[List[str]]
    time_breakdown: Dict[str, int]
    optimization_opportunities: List[str]


class LearningInsightsResponse(BaseModel):
    """API response model for agent learning insights."""
    agent_name: str
    learning_summary: Dict[str, Any]
    active_patterns: List[Dict[str, Any]]
    pattern_effectiveness: Dict[str, float]
    recommended_training: List[str]
    confidence_trends: List[Dict[str, float]]


# Enhanced TRA_DATA Integration Response Models

class RiskAreaOverviewResponse(BaseModel):
    """API response model for risk area overview."""
    risk_area: str
    status: RiskAreaStatus
    completion_percentage: float
    questions_answered: int
    total_questions: int
    priority_level: str
    estimated_effort_hours: Optional[float]
    last_activity: Optional[datetime]


class EnhancedTRAResponse(BaseModel):
    """API response model for enhanced TRA assessments."""
    tra_id: str
    title: str
    project_name: Optional[str]
    business_unit: str
    overall_status: AssessmentState
    overall_completion: float
    risk_areas: List[RiskAreaOverviewResponse]
    target_completion_date: Optional[datetime]
    quality_score: Optional[float]
    next_priority_area: Optional[str]


class TRACompletionMatrixResponse(BaseModel):
    """API response model for TRA completion matrix."""
    tra_id: str
    completion_matrix: Dict[str, float]
    overall_completion: float
    completed_areas: List[str]
    in_progress_areas: List[str]
    not_started_areas: List[str]
    estimated_remaining_hours: Optional[float]
    projected_completion_date: Optional[datetime]


class TRARecommendationsResponse(BaseModel):
    """API response model for AI-powered TRA recommendations."""
    tra_id: str
    next_recommended_action: str
    priority_areas: List[str]
    optimization_suggestions: List[str]
    document_recommendations: List[str]
    estimated_session_time: Optional[int]
    efficiency_tips: List[str]
