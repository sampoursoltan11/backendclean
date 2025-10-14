"""
Document Processing Tools - Strands 1.x Compatible
Tools for document analysis, RAG, and risk area identification
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from strands import tool

from backend.services.bedrock_kb_service import BedrockKnowledgeBaseService
from backend.services.file_tracking_service import FileTrackingService
from backend.core.config import get_settings
import boto3
import json

logger = logging.getLogger(__name__)


# Initialize services
_kb_service: Optional[BedrockKnowledgeBaseService] = None
_file_tracker: Optional[FileTrackingService] = None

def get_kb_service() -> BedrockKnowledgeBaseService:
    """Get singleton Knowledge Base service."""
    global _kb_service
    if _kb_service is None:
        _kb_service = BedrockKnowledgeBaseService()
    return _kb_service

def get_file_tracker() -> FileTrackingService:
    """Get singleton File Tracking service."""
    global _file_tracker
    if _file_tracker is None:
        _file_tracker = FileTrackingService()
    return _file_tracker


@tool
async def search_knowledge_base(
    query: str,
    assessment_id: str,
    max_results: int = 5
) -> str:
    """
    Search uploaded documents using AWS Bedrock Knowledge Base.
    
    Args:
        query: Search query or question
        session_id: Session ID for context
        max_results: Maximum number of results to return
    
    Returns:
        String with search results and answer
    """
    try:
        kb = get_kb_service()
        # Enforce readiness check before querying KB
        # (Assume assessment_id is also the ingestion job id for simplicity, or adapt as needed)
        # In a real system, you may need to map assessment_id to the latest ingestion_job_id for the document(s)
        # Here, we check readiness for the whole assessment's KB folder
        # If you want per-file readiness, adapt to check by file/ingestion_job_id
        if hasattr(kb, 'get_knowledge_base_status'):
            kb_status = await kb.get_knowledge_base_status()
            if not kb_status.get('success'):
                return f"Knowledge base is not available: {kb_status.get('error', 'Unknown error')}"
        # Optionally, check for at least one indexed session/document
        # If not ready, return a clear message
        if hasattr(kb, 'get_knowledge_base_status') and kb_status.get('indexed_sessions', 0) == 0:
            return "⏳ The knowledge base is still ingesting documents. Please wait until the hourglass turns green (Ready) before searching."
        # Proceed with search
        result = await kb.retrieve_and_generate(
            query=query,
            assessment_id=assessment_id,
            context={"max_results": max_results}
        )
        if result.get("status") == "success":
            response = result.get("response", "No information found.")
            citations = result.get("citations", [])
            formatted_response = f"{response}\n\n"
            if citations:
                formatted_response += "**Sources:**\n"
                for i, citation in enumerate(citations[:3], 1):
                    source = citation.get("source", "Unknown")
                    formatted_response += f"{i}. {source}\n"
            return formatted_response
        else:
            return f"Search encountered an issue: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


@tool
async def analyze_document_content(
    filename: str,
    assessment_id: str,
    analysis_type: str = "comprehensive"
) -> dict:
    """
    Analyze document content for specific information.
    
    Args:
        filename: Name of the document to analyze
        session_id: Session ID where document was uploaded
        analysis_type: Type of analysis (comprehensive, security, compliance, technical)
    
    Returns:
        Dictionary with analysis results
    """
    try:
        kb = get_kb_service()
        # Enforce readiness check before analysis
        if hasattr(kb, 'get_knowledge_base_status'):
            kb_status = await kb.get_knowledge_base_status()
            if not kb_status.get('success'):
                return {
                    "success": False,
                    "error": f"Knowledge base is not available: {kb_status.get('error', 'Unknown error')}"
                }
        if hasattr(kb, 'get_knowledge_base_status') and kb_status.get('indexed_sessions', 0) == 0:
            return {
                "success": False,
                "error": "⏳ The knowledge base is still ingesting documents. Please wait until the hourglass turns green (Ready) before analysis."
            }
        # Create analysis query based on type
        analysis_queries = {
            "comprehensive": f"Provide a comprehensive analysis of the document {filename}. Include key topics, important details, and main findings.",
            "security": f"Analyze {filename} for security-related information, including security controls, threats, vulnerabilities, and protective measures mentioned.",
            "compliance": f"Identify compliance requirements, regulatory standards, and legal obligations mentioned in {filename}.",
            "technical": f"Extract technical architecture details, system components, technologies, and infrastructure information from {filename}."
        }
        query = analysis_queries.get(analysis_type, analysis_queries["comprehensive"])
        result = await kb.retrieve_and_generate(
            query=query,
            assessment_id=assessment_id,
            context={"filename": filename, "analysis_type": analysis_type}
        )
        if result.get("status") == "success":
            return {
                "success": True,
                "filename": filename,
                "analysis_type": analysis_type,
                "analysis": result.get("response", ""),
                "confidence": result.get("confidence", 0.0)
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Analysis failed")
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def suggest_risk_areas_from_documents(assessment_id: str) -> dict:
    """
    Analyze uploaded documents from DynamoDB and suggest applicable TRA risk areas.
    Reads document summaries directly from DynamoDB (NO KB query needed).
    
    This tool identifies which TRA risk areas apply based on document content:
    - Data Security (PII, sensitive data, privacy)
    - Infrastructure Security (cloud, networks, hosting)
    - Application Security (software, APIs, authentication)
    - Compliance & Regulatory (GDPR, HIPAA, standards)
    - Business Continuity (DR, backup, availability)
    - Vendor & Third-Party Risk (external dependencies)
    
    Args:
        assessment_id: Assessment ID to analyze documents for
    
    Returns:
        Dictionary with suggested risk areas and evidence
    """
    try:
        from backend.services.dynamodb_service import DynamoDBService
        db = DynamoDBService()
        
        # Get documents from DynamoDB
        documents = await db.get_documents_by_assessment(assessment_id)
        
        if not documents:
            return {
                "success": False,
                "error": "No documents found for this assessment",
                "suggested_risk_areas": []
            }
        
        # Extract summaries and topics (already in DynamoDB!)
        summaries = []
        all_topics = set()
        
        for doc in documents:
            summary = doc.get('content_summary', '')
            if summary:
                summaries.append(summary)
            
            # Extract tags/topics
            topics = doc.get('tags', [])
            if isinstance(topics, list):
                for topic in topics:
                    if isinstance(topic, str):
                        all_topics.add(topic.lower())
                    elif isinstance(topic, dict):
                        all_topics.add(topic.get('S', '').lower())
        
        # Combine all text for analysis
        combined_text = ' '.join(summaries).lower()
        
        # Define risk area patterns - MUST match decision_tree2.yaml risk area names EXACTLY
        risk_patterns = {
            'Third Party Risk': {
                'keywords': ['vendor', 'third party', '3rd party', 'supplier', 'third-party',
                            'integration', 'external', 'partner', 'contract', 'procurement',
                            'owning', 'designing', 'deploying', 'operating'],
                'weight': 1.0
            },
            'Data Privacy Risk': {
                'keywords': ['pii', 'personal data', 'gdpr', 'privacy', 'sensitive data',
                            'data classification', 'confidential', 'customer data',
                            'personal information', 'sensitive information', 'data protection'],
                'weight': 1.0
            },
            'AI Risk': {  # ← FIXED: Was "Artificial Intelligence", now matches decision_tree2.yaml
                'keywords': ['ai', 'artificial intelligence', 'machine learning', 'ml',
                            'neural network', 'deep learning', 'generative', 'llm',
                            'algorithm', 'automated decision', 'model', 'training', 'ai-assisted'],
                'weight': 1.0
            },
            'IP Risk': {  # ← FIXED: Was "Intellectual Property", now matches decision_tree2.yaml
                'keywords': ['intellectual property', 'ip', 'patent', 'copyright',
                            'trademark', 'software development', 'custom solution', 'proprietary',
                            'new process', 'new technology', 'digital solution', 'develop software'],
                'weight': 1.0
            }
        }
        
        # Analyze and score each risk area
        suggested_areas = []
        evidence = {}

        import sys
        print(f"\n===== RISK SUGGESTION ANALYSIS =====", file=sys.stderr)
        print(f"Combined text (first 300 chars): {combined_text[:300]}", file=sys.stderr)
        print(f"All topics: {all_topics}", file=sys.stderr)
        print(f"=====================================\n", file=sys.stderr)

        for risk_area, config in risk_patterns.items():
            keywords = config['keywords']
            weight = config['weight']

            # Count keyword matches
            matches = sum(1 for kw in keywords if kw in combined_text or kw in all_topics)
            score = matches * weight

            print(f"{risk_area}: {matches} matches (score={score})", file=sys.stderr)

            # If significant matches, suggest this area
            if score >= 1.0:  # At least 1 keyword match
                suggested_areas.append(risk_area)
                print(f"  ✓ ADDED: {risk_area}", file=sys.stderr)
                
                # Extract evidence from matching summary
                matching_summary = next(
                    (s for s in summaries if any(kw in s.lower() for kw in keywords)),
                    ''
                )
                
                if matching_summary:
                    evidence[risk_area] = matching_summary[:200]
                else:
                    evidence[risk_area] = f"Keywords found: {', '.join([kw for kw in keywords if kw in combined_text][:3])}"
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "suggested_risk_areas": suggested_areas,
            "evidence": evidence,
            "documents_analyzed": len(documents),
            "message": f"Analyzed {len(documents)} documents, identified {len(suggested_areas)} applicable risk areas"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "suggested_risk_areas": []
        }


async def generate_document_summary(file_content: str, filename: str) -> Dict[str, Any]:
    """
    Generate a concise <150 word summary of document using fast LLM.
    
    Args:
        file_content: Text content of the document
        filename: Name of the file being summarized
    
    Returns:
        Dictionary with summary and key details
    """
    try:
        settings = get_settings()
        
        # Use Bedrock Runtime for fast summarization
        bedrock = boto3.client(
            'bedrock-runtime',
            region_name=settings.bedrock_region
        )
        
        # Limit content to first 4000 characters for speed
        content_sample = file_content[:4000] if len(file_content) > 4000 else file_content
        
        prompt = f"""You are analyzing a document for a TECHNOLOGY RISK ASSESSMENT (TRA).  
Extract only the key factual details needed to understand potential technology, security, and compliance risks.  
Do not interpret, explain, or summarize generally — focus only on concrete facts stated in the document.

Summarize the document in UNDER 180 WORDS, using the following exact structure and section order:  

1. Technology Risks - vulnerabilities, threats, weaknesses, or potential risk areas.
2. Technical Architecture - key systems, applications, platforms, databases, or APIs.
3. Data Handling & Privacy - how data (especially personal or sensitive) is collected, stored, processed, or shared.
4. Security Controls - authentication, encryption, access control, or other protection mechanisms.
5. Compliance & Standards - frameworks, policies, or regulations (e.g., GDPR, ISO 27001, SOC2).
6. Infrastructure & Cloud - cloud providers, hosting environments, network or regional details.
7. Integrations & Third Parties - vendors, external APIs, or service dependencies.


Rules:  
- Use bullet points under each section.  
- If a section has no information, write “None.”  
- Keep total summary under 180 words.  
- Do not include text outside this structure.

Document: {filename}  
Content:  
{content_sample}

Provide a structured, technology risk-focused summary following the format above."""
        
        # Call Bedrock with fast model
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock.invoke_model(
            modelId=settings.bedrock_summary_model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        summary = response_body['content'][0]['text']
        
        # Extract key topics from summary
        key_topics = []
        keywords = ['aws', 'azure', 'gcp', 'cloud', 'api', 'database', 'encryption', 
                   'authentication', 'pii', 'gdpr', 'hipaa', 'compliance', 'backup', 'security']
        
        summary_lower = summary.lower()
        for keyword in keywords:
            if keyword in summary_lower:
                key_topics.append(keyword)
        
        return {
            "success": True,
            "summary": summary.strip(),
            "key_topics": key_topics[:10],  # Limit to 10 topics
            "word_count": len(summary.split())
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "summary": f"Error generating summary for {filename}"
        }


@tool
async def upload_document_metadata(
    filename: str,
    session_id: str,
    file_id: str,
    project_name: str = None,
    tags: List[str] = None
) -> dict:
    """
    Record document upload metadata for tracking.
    
    Args:
        filename: Original filename
        session_id: Session ID
        file_id: Unique file identifier
        project_name: Associated project name
        tags: Document tags for categorization
    
    Returns:
        Dictionary with metadata confirmation
    """
    try:
        file_tracker = get_file_tracker()
        
        # Create metadata record
        metadata = {
            "file_id": file_id,
            "filename": filename,
            "session_id": session_id,
            "project_name": project_name,
            "tags": tags or [],
            "uploaded_at": datetime.utcnow().isoformat(),
            "status": "uploaded"
        }
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": filename,
            "metadata": metadata
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
