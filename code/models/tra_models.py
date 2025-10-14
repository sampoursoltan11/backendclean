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
# Note: RiskAreaSegment and EnhancedTRAAssessment models were removed as they are not used in production


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
# Note: AgentDecisionType and AgentPerformanceMetric enums were removed as they are not used in production


class ConversationPhase(str, Enum):
    """Phases of conversation."""
    INITIATION = "initiation"
    INFORMATION_GATHERING = "information_gathering"
    DOCUMENT_PROCESSING = "document_processing"
    ASSESSMENT_BUILDING = "assessment_building"
    CLARIFICATION = "clarification"
    REVIEW_PREPARATION = "review_preparation"
    COMPLETION = "completion"


# Note: AgentDecision, ConversationContext, and AgentPerformanceMetrics models were removed as they are not used in production

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


# Note: RAGRetrievalRecord, DecisionTreeAnalytics, and AgentLearningRecord models were removed as they are not used in production


# Enhanced API Response Models
# Note: All analytics response models (AgentPerformanceResponse, ConversationInsightsResponse,
# RAGPerformanceResponse, DecisionAnalyticsResponse, LearningInsightsResponse, RiskAreaOverviewResponse,
# EnhancedTRAResponse, TRACompletionMatrixResponse, TRARecommendationsResponse) were removed as
# they are not used by any API endpoints in production
