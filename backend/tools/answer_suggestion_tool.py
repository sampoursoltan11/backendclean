"""
Answer Suggestion Tool - RAG-powered answer recommendations
Suggests answers to TRA questions based on uploaded document context
"""

import logging
from typing import Dict, Any, Optional
from strands import tool

from backend.services.bedrock_kb_service import BedrockKnowledgeBaseService
from backend.services.dynamodb_service import DynamoDBService
from backend.core.config import get_settings

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize services
_kb_service: Optional[BedrockKnowledgeBaseService] = None
_db_service: Optional[DynamoDBService] = None

def get_kb_service() -> BedrockKnowledgeBaseService:
    """Get singleton KB service."""
    global _kb_service
    if _kb_service is None:
        _kb_service = BedrockKnowledgeBaseService()
    return _kb_service

def get_db_service() -> DynamoDBService:
    """Get singleton DynamoDB service."""
    global _db_service
    if _db_service is None:
        _db_service = DynamoDBService()
    return _db_service


@tool
async def suggest_answer_from_context(
    assessment_id: str,
    question_text: str,
    question_type: str = "text",
    options: list = None
) -> dict:
    """
    Provide technical suggestions for TRA questions based on uploaded document summaries.
    
    Uses document summaries from DynamoDB and LLM analysis to provide high-level 
    technical guidance and considerations (not direct answers).
    
    Args:
        assessment_id: TRA assessment identifier
        question_text: The question being asked
        question_type: Type of question (text, select, multiselect, number)
        options: Available options for select/multiselect questions
    
    Returns:
        Dictionary with technical suggestions and guidance
    """
    try:
        db = get_db_service()
        
        # Get documents with summaries from DynamoDB
        documents = await db.get_documents_by_assessment(assessment_id)
        
        if not documents:
            return {
                "success": True,
                "has_suggestion": False,
                "message": "No documents available for analysis. Consider uploading project documentation."
            }
        
        # Extract summaries and metadata
        document_summaries = []
        for doc in documents:
            summary = doc.get('content_summary', '')
            filename = doc.get('filename', 'document')
            tags = doc.get('tags', [])

            # Convert DynamoDB format tags to simple strings
            # Tags can be in format [{'S': 'azure'}, ...] or ['azure', ...]
            topics = []
            for tag in tags:
                if isinstance(tag, dict) and 'S' in tag:
                    topics.append(tag['S'])
                elif isinstance(tag, str):
                    topics.append(tag)

            if summary and summary.strip():
                document_summaries.append({
                    'filename': filename,
                    'summary': summary,
                    'topics': topics
                })
        
        if not document_summaries:
            return {
                "success": True,
                "has_suggestion": False,
                "message": "No document summaries available for analysis."
            }
        
        # Generate technical suggestion using LLM
        suggestion = await _generate_technical_suggestion(
            question_text=question_text,
            question_type=question_type,
            options=options,
            document_summaries=document_summaries
        )
        
        if not suggestion or not suggestion.get('has_suggestion'):
            # Fallback: Always provide some technical guidance
            suggestion = await _generate_fallback_suggestion(
                question_text=question_text,
                question_type=question_type,
                options=options,
                document_summaries=document_summaries
            )
        
        return {
            "success": True,
            "has_suggestion": True,
            "suggested_answer": suggestion.get('technical_guidance'),
            "confidence": suggestion.get('confidence', 'medium'),
            "supporting_context": suggestion.get('supporting_context', []),
            "reasoning": suggestion.get('reasoning'),
            "message": f"Technical guidance based on {len(document_summaries)} document(s)"
        }
        
    except Exception as e:
        logger.debug(f"Error: {e}")
        return {
            "success": False,
            "has_suggestion": False,
            "error": str(e)
        }


async def _generate_technical_suggestion(
    question_text: str,
    question_type: str,
    options: list,
    document_summaries: list
) -> dict:
    """Generate technical suggestion using LLM analysis of document summaries."""
    try:
        import aioboto3
        import json
        from backend.core.config import get_settings

        settings = get_settings()

        # Prepare document context
        doc_context = ""
        for i, doc in enumerate(document_summaries, 1):
            doc_context += f"\n**Document {i}: {doc['filename']}**\n"
            doc_context += f"Summary: {doc['summary'][:500]}...\n"
            if doc['topics']:
                doc_context += f"Key Topics: {', '.join(doc['topics'][:5])}\n"

        # Prepare options context for select questions
        options_context = ""
        if options and question_type in ["select", "multiselect"]:
            options_list = []
            for opt in options:
                if isinstance(opt, str):
                    options_list.append(opt)
                elif isinstance(opt, dict):
                    options_list.append(opt.get('label', opt.get('value', str(opt))))
            options_context = f"\nAvailable Options: {', '.join(options_list)}"

        # Create LLM prompt for technical guidance - focused on brevity and key details
        prompt = f"""You are a TRA expert. Provide SHORT, SPECIFIC technical guidance for this question.

**QUESTION:** {question_text}
{options_context}

**DOCUMENTS:**
{doc_context}

**INSTRUCTIONS:**
- Answer in 2-3 concise sentences maximum
- Use ONLY specific details from the documents (system names, technologies, data types)
- Be direct and actionable
- No generic phrases

**EXAMPLES:**

Q: "What data is processed?"
Docs mention: "Azure Data Lake, customer PII, financial records"
Response: "The system processes customer PII and financial records in Azure Data Lake Gen2. Implement role-based access controls and audit logging."

Q: "What backup exists?"
Docs mention: "ETL pipelines, Recovery Vault"
Response: "ETL pipelines use Azure Recovery Vault for backups. Test recovery procedures regularly and implement cross-region replication."

**JSON FORMAT:**
{{
    "has_suggestion": true,
    "technical_guidance": "2-3 short sentences with specific document details",
    "confidence": "high/medium/low",
    "reasoning": "One brief sentence",
    "supporting_context": ["Detail 1", "Detail 2"]
}}

JSON response:"""

        # Call Bedrock using async client
        logger.info(f"[SUGGESTION DEBUG] Calling Bedrock with model: {settings.bedrock_model_id}")
        logger.info(f"[SUGGESTION DEBUG] Document summaries: {len(document_summaries)} docs")
        logger.info(f"[SUGGESTION DEBUG] Prompt length: {len(prompt)} chars")

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "temperature": 0.4,
            "messages": [{"role": "user", "content": prompt}]
        }

        # Use async Bedrock client
        session = aioboto3.Session()
        async with session.client('bedrock-runtime', region_name=settings.bedrock_region) as bedrock:
            response = await bedrock.invoke_model(
                modelId=settings.bedrock_model_id,
                body=json.dumps(request_body)
            )

            response_body = json.loads(await response['body'].read())
            ai_response = response_body['content'][0]['text']

        logger.info(f"[SUGGESTION DEBUG] Bedrock response length: {len(ai_response)} chars")
        logger.info(f"[SUGGESTION DEBUG] Response preview: {ai_response[:200]}...")
        
        # Parse JSON response
        try:
            # Extract JSON from response (handle potential markdown formatting)
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                suggestion = json.loads(json_match.group(0))
            else:
                suggestion = json.loads(ai_response)
            
            # Validate response structure
            if not isinstance(suggestion, dict) or not suggestion.get('has_suggestion'):
                logger.warning(f"[SUGGESTION DEBUG] Invalid suggestion structure, falling back")
                return {"has_suggestion": False}

            # Check if response is generic/useless
            guidance_text = suggestion.get('technical_guidance', '').lower()
            generic_phrases = [
                'technical architecture, security requirements, and operational processes',
                'consider the technical architecture',
                'security requirements and operational processes'
            ]
            is_generic = any(phrase in guidance_text for phrase in generic_phrases)

            if is_generic:
                logger.warning(f"[SUGGESTION DEBUG] LLM returned generic response, falling back")
                return {"has_suggestion": False}

            logger.info(f"[SUGGESTION DEBUG] Valid specific suggestion returned")
            return suggestion
            
        except json.JSONDecodeError:
            # Fallback: use raw text as guidance
            return {
                "has_suggestion": True,
                "technical_guidance": ai_response.strip(),
                "confidence": "medium",
                "reasoning": "Based on analysis of project documentation",
                "supporting_context": [f"Analysis of {len(document_summaries)} document(s)"]
            }
        
    except Exception as e:
        import traceback
        logger.error(f"[SUGGESTION DEBUG] LLM generation error: {e}")
        logger.error(f"[SUGGESTION DEBUG] Error type: {type(e).__name__}")
        logger.error(f"[SUGGESTION DEBUG] Traceback: {traceback.format_exc()}")
        return {"has_suggestion": False, "error": str(e)}


async def _generate_fallback_suggestion(
    question_text: str,
    question_type: str,
    options: list,
    document_summaries: list
) -> dict:
    """Generate intelligent technical guidance by analyzing document summaries and questions."""
    try:
        logger.info(f"[FALLBACK DEBUG] Generating intelligent fallback for question: {question_text[:100]}...")
        
        # Extract content from document summaries
        all_topics = []
        all_summaries = []
        for doc in document_summaries:
            all_topics.extend(doc.get('topics', []))
            if doc.get('summary'):
                all_summaries.append(doc.get('summary', ''))
        
        # Combine all document content
        combined_content = ' '.join(all_summaries).lower()
        question_lower = question_text.lower()

        logger.info(f"[FALLBACK DEBUG] Document content length: {len(combined_content)}, Topics: {all_topics[:5]}")
        
        # Intelligent content analysis
        guidance_parts = []
        specific_references = []
        
        # Analyze document content for specific technologies/systems
        # AWS
        if 'aws' in combined_content or 'amazon' in combined_content:
            if 'security' in question_lower or 'access' in question_lower or 'authentication' in question_lower:
                guidance_parts.append("Based on your AWS infrastructure, consider implementing IAM policies and security groups")
                specific_references.append("AWS services mentioned in your documentation")
            elif 'backup' in question_lower or 'recovery' in question_lower:
                guidance_parts.append("For your AWS environment, evaluate S3 backup strategies and cross-region replication")
                specific_references.append("AWS architecture described in documents")

        # Azure
        if 'azure' in combined_content or 'microsoft' in combined_content:
            if 'security' in question_lower or 'access' in question_lower or 'authentication' in question_lower:
                guidance_parts.append("Based on your Azure infrastructure, ensure Azure AD role-based access controls and implement Conditional Access policies")
                specific_references.append("Azure services mentioned in your documentation")
            elif 'backup' in question_lower or 'recovery' in question_lower:
                guidance_parts.append("For your Azure environment, leverage Azure Backup and geo-redundant storage for disaster recovery")
                specific_references.append("Azure architecture described in documents")
            elif 'data' in question_lower or 'privacy' in question_lower:
                if 'data lake' in combined_content or 'synapse' in combined_content or 'data factory' in combined_content:
                    guidance_parts.append("Your Azure data platform (Data Lake/Synapse/Data Factory) requires data classification, encryption, and access logging")
                    specific_references.append("Azure data services identified in your documents")

        # GCP
        if 'gcp' in combined_content or 'google cloud' in combined_content:
            if 'security' in question_lower or 'access' in question_lower:
                guidance_parts.append("For your GCP environment, implement IAM policies and Cloud Identity for access management")
                specific_references.append("GCP services mentioned in your documentation")
            elif 'backup' in question_lower or 'recovery' in question_lower:
                guidance_parts.append("Your GCP infrastructure should leverage Cloud Storage for backups and multi-region replication")
                specific_references.append("GCP architecture described in documents")
        
        if 'api' in combined_content or 'rest' in combined_content or 'endpoint' in combined_content:
            if 'security' in question_lower or 'access' in question_lower:
                guidance_parts.append("Your API architecture requires proper authentication middleware and rate limiting")
                specific_references.append("API endpoints described in your documents")
            elif 'monitoring' in question_lower:
                guidance_parts.append("For the APIs described in your documentation, implement comprehensive logging and monitoring")
                specific_references.append("API services outlined in your architecture")
        
        if 'database' in combined_content or 'sql' in combined_content or 'nosql' in combined_content:
            if 'security' in question_lower or 'access' in question_lower:
                guidance_parts.append("Your database architecture requires encryption at rest and proper access controls")
                specific_references.append("Database systems mentioned in your documents")
            elif 'backup' in question_lower:
                guidance_parts.append("For your database systems, ensure automated backups and point-in-time recovery")
                specific_references.append("Database infrastructure from your documentation")
        
        if 'cloud' in combined_content:
            if 'compliance' in question_lower:
                guidance_parts.append("Your cloud infrastructure should align with relevant compliance frameworks")
                specific_references.append("Cloud architecture outlined in your documents")
        
        if 'docker' in combined_content or 'container' in combined_content or 'kubernetes' in combined_content:
            if 'security' in question_lower:
                guidance_parts.append("Your containerized environment requires image scanning and runtime security")
                specific_references.append("Container architecture from your documentation")
        
        # Fall back to topic-based guidance if no specific content matches
        if not guidance_parts and all_topics:
            if any(topic.lower() in ['cloud', 'aws', 'azure'] for topic in all_topics):
                if 'security' in question_lower:
                    guidance_parts.append("Based on your cloud architecture, consider implementing proper identity and access management")
                    specific_references.append(f"Cloud topics: {', '.join([t for t in all_topics if t.lower() in ['cloud', 'aws', 'azure']][:2])}")
            
            if any(topic.lower() in ['api', 'application'] for topic in all_topics):
                if 'security' in question_lower:
                    guidance_parts.append("Your application architecture should implement proper authentication and authorization")
                    specific_references.append(f"Application topics: {', '.join([t for t in all_topics if t.lower() in ['api', 'application']][:2])}")
        
        # Question-specific fallbacks with document context
        if not guidance_parts:
            if 'backup' in question_lower or 'recovery' in question_lower:
                guidance_parts.append("Based on your system architecture, evaluate backup strategies and disaster recovery procedures")
                specific_references.append("System architecture from your uploaded documents")
            elif 'monitoring' in question_lower or 'logging' in question_lower:
                guidance_parts.append("For your technical environment, implement comprehensive monitoring and logging")
                specific_references.append("Technical details from your documentation")
            elif 'access' in question_lower or 'authentication' in question_lower:
                guidance_parts.append("Your system architecture requires proper access controls and authentication mechanisms")
                specific_references.append("System design from your uploaded documents")
            elif 'compliance' in question_lower:
                guidance_parts.append("Based on your project requirements, ensure compliance with relevant regulatory frameworks")
                specific_references.append("Project requirements from your documentation")
        
        # Final fallback - but still reference documents
        if not guidance_parts:
            if len(document_summaries) > 0:
                guidance_parts.append(f"Based on your {document_summaries[0]['filename']} and project architecture, consider the security and operational requirements specific to your environment")
                specific_references.append(f"Project details from {len(document_summaries)} uploaded document(s)")
            else:
                guidance_parts.append("Consider your system's technical architecture, security requirements, and operational processes")
                specific_references.append("General TRA best practices")
        
        # Combine guidance
        technical_guidance = ". ".join(guidance_parts)
        if len(technical_guidance) > 250:
            technical_guidance = technical_guidance[:250] + "..."

        logger.info(f"[FALLBACK DEBUG] Generated guidance: {technical_guidance[:100]}...")
        
        return {
            "has_suggestion": True,
            "technical_guidance": technical_guidance,
            "confidence": "medium" if specific_references else "low",
            "reasoning": f"Analysis of your project documentation combined with TRA question context",
            "supporting_context": specific_references[:3] if specific_references else [f"General analysis of {len(document_summaries)} document(s)"]
        }
        
    except Exception as e:
        import traceback
        logger.error(f"[FALLBACK DEBUG] Error in fallback: {e}")
        logger.error(f"[FALLBACK DEBUG] Traceback: {traceback.format_exc()}")
        # Ultimate fallback - but still try to reference documents
        doc_ref = f"your {document_summaries[0]['filename']}" if document_summaries else "your system"
        return {
            "has_suggestion": True,
            "technical_guidance": f"Based on {doc_ref}, consider the technical architecture, security requirements, and operational processes relevant to this question.",
            "confidence": "low",
            "reasoning": "General technical guidance based on your uploaded documentation",
            "supporting_context": [f"Analysis of {len(document_summaries)} document(s)" if document_summaries else "General TRA considerations"]
        }


def _generate_answer_suggestion(
    question_text: str,
    question_type: str,
    options: list,
    context: list,
    confidence: str
) -> Optional[str]:
    """
    Generate answer suggestion based on context and question type.
    
    Uses simple keyword matching and context analysis.
    For production, this could use LLM for more sophisticated analysis.
    """
    if not context or confidence == "low":
        return None
    
    # Combine all context text
    combined_context = " ".join([c["text"].lower() for c in context])
    
    # For select questions, match against options
    if question_type in ["select", "multiselect"] and options:
        # Find best matching option
        best_match = None
        best_score = 0
        
        for option in options:
            option_value = option if isinstance(option, str) else option.get("value", "")
            option_label = option if isinstance(option, str) else option.get("label", "")
            
            # Count keyword matches
            keywords = option_label.lower().split()
            score = sum(1 for keyword in keywords if keyword in combined_context)
            
            if score > best_score:
                best_score = score
                best_match = option_value
        
        if best_score > 0:
            return best_match
    
    # For text questions, extract relevant snippet
    elif question_type == "text":
        # Look for key information patterns
        question_lower = question_text.lower()
        
        if "how many" in question_lower or "number of" in question_lower:
            # Extract numbers from context
            import re
            numbers = re.findall(r'\d+', combined_context)
            if numbers:
                return numbers[0]
        
        # Return most relevant excerpt (first 100 chars of highest scored context)
        if context:
            return context[0]["text"][:100].strip()
    
    return None


def _generate_reasoning(
    question_text: str,
    suggested_answer: str,
    context: list
) -> str:
    """Generate human-readable reasoning for the suggestion."""
    if not context:
        return "Based on general context"
    
    sources = [c.get("source", "document") for c in context]
    unique_sources = list(set(sources))
    
    if len(unique_sources) == 1:
        source_text = f"your {unique_sources[0]}"
    elif len(unique_sources) == 2:
        source_text = f"your {unique_sources[0]} and {unique_sources[1]}"
    else:
        source_text = "your uploaded documents"
    
    return f"Based on {source_text}, which mentions relevant information about this question"
