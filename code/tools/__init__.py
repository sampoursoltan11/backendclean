"""
TRA System Tools - Strands 1.x Compatible
Shared tools used by both Simple and Enhanced TRA variants
"""

from .assessment_tools import (
    create_assessment,
    update_assessment,
    list_assessments,
    get_assessment,
    switch_assessment
)

from .document_tools import (
    search_knowledge_base,
    analyze_document_content,
    suggest_risk_areas_from_documents,
    upload_document_metadata
)

from .question_tools import (
    question_flow,
)

from .status_tools import (
    get_assessment_summary,
    check_status,
    review_answers,
    generate_assessor_link,
    export_assessment,
    update_state,
    list_kb_items
)

from .risk_area_tools import (
    add_risk_area,
    remove_risk_area,
    set_risk_areas,
    link_document
)

from .answer_suggestion_tool import (
    suggest_answer_from_context
)

__all__ = [
    # Assessment tools
    'create_assessment',
    'update_assessment',
    'list_assessments',
    'get_assessment',
    'switch_assessment',
    
    # Document tools
    'search_knowledge_base',
    'analyze_document_content',
    'suggest_risk_areas_from_documents',
    'upload_document_metadata',
    
    # Question tools
    'question_flow',
    
    # Status tools
    'get_assessment_summary',
    'check_status',
    'review_answers',
    'generate_assessor_link',
    'export_assessment',
    'update_state',
    'list_kb_items',
    
    # Risk area & document tools
    'add_risk_area',
    'remove_risk_area',
    'set_risk_areas',
    'link_document',
    
    # Answer suggestion
    'suggest_answer_from_context',
]
