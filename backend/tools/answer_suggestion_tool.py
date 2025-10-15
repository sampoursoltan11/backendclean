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


def rephrase_question_for_llm(question_text: str) -> str:
    """
    Rephrase statement-like questions into proper question format for better LLM understanding.

    Examples:
    - "Vendor Supplier name" -> "What is the vendor supplier name?"
    - "Has the contract being signed" -> "Has the contract been signed?"
    - "Will your Project create a new product" -> "Will your project create a new product or process?"

    Args:
        question_text: Original question text from YAML

    Returns:
        Rephrased question text
    """
    q = question_text.strip()

    # Already a proper question
    if q.endswith('?'):
        return q

    # Convert statement-style questions to proper questions
    q_lower = q.lower()

    # Pattern 1: Single words or short phrases (likely asking for information)
    # E.g., "Vendor Supplier name", "Application Description", "Business Application Owner"
    if len(q.split()) <= 5 and not any(word in q_lower for word in ['will', 'does', 'is', 'are', 'has', 'have', 'can', 'could', 'would', 'should']):
        # Check for common patterns
        if 'name' in q_lower:
            return f"What is the {q.lower()}?"
        elif any(word in q_lower for word in ['description', 'details', 'objective', 'scope', 'context']):
            return f"What is the {q.lower()}?"
        elif 'date' in q_lower:
            return f"What is the {q.lower()}?"
        elif 'owner' in q_lower:
            return f"Who is the {q.lower()}?"
        else:
            return f"What is the {q}?"

    # Pattern 2: Statement that should be a question
    # E.g., "New Access Is granted only to approved persons"
    if any(q_lower.startswith(word) for word in ['new ', 'access ', 'all ', 'document ', 'controls ', 'testing ']):
        # Likely a compliance statement asking for confirmation
        return f"Is it true that {q.lower()}?"

    # Pattern 3: Incomplete yes/no questions missing question mark
    # E.g., "Has the contract being signed"
    if any(q_lower.startswith(word) for word in ['will ', 'does ', 'is ', 'are ', 'has ', 'have ', 'can ', 'could ', 'would ', 'should ']):
        return f"{q}?"

    # Pattern 4: Imperative statements asking for verification
    # E.g., "Verify that...", "Confirm that...", "Check the..."
    if any(q_lower.startswith(word) for word in ['verify ', 'confirm ', 'check ', 'provide ', 'explain ']):
        if q_lower.startswith('verify '):
            thing = q[len('verify '):].strip()
            return f"Have you verified that {thing}?"
        elif q_lower.startswith('confirm '):
            thing = q[len('confirm '):].strip()
            return f"Have you confirmed that {thing}?"
        elif q_lower.startswith('check '):
            thing = q[len('check '):].strip()
            return f"Have you checked {thing}?"
        elif q_lower.startswith('provide '):
            thing = q[len('provide '):].strip()
            # Remove "please" and extra whitespace
            thing = thing.replace('please', '').replace('Please', '').strip()
            # Remove "a brief summary of" -> just ask for it directly
            if thing.startswith('a '):
                thing = thing[2:]
            return f"What is the {thing}?"
        elif q_lower.startswith('explain '):
            thing = q[len('explain '):].strip()
            return f"Can you explain {thing}?"

    # Default: Add "Please provide" for free-text fields
    return f"Please provide: {q}"


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

        # Rephrase question for better LLM understanding
        rephrased_question = rephrase_question_for_llm(question_text)
        logger.info(f"[SUGGESTION] Original question: {question_text}")
        logger.info(f"[SUGGESTION] Rephrased question: {rephrased_question}")

        # Prepare document context with more detail
        doc_context = ""
        for i, doc in enumerate(document_summaries, 1):
            doc_context += f"\n**Document {i}: {doc['filename']}**\n"
            # Increase summary length from 500 to 1000 chars for better context
            summary_text = doc['summary'][:1000]
            if len(doc['summary']) > 1000:
                summary_text += "..."
            doc_context += f"Summary: {summary_text}\n"
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

        # Create LLM prompt for direct, concise answers using rephrased question
        prompt = f"""You are a TRA expert. Answer the question below ONLY using specific facts from the user's documents.

**YOUR TASK:**
Analyze the DOCUMENTS section below and answer the QUESTION with ONE sentence (12-20 words max).

**QUESTION TO ANSWER:**
{rephrased_question}
{options_context}

**DOCUMENTS TO ANALYZE:**
{doc_context}

**CRITICAL INSTRUCTIONS:**
1. READ THE DOCUMENTS ABOVE - Find specific facts that answer this question
2. ONE sentence maximum (12-20 words)
3. ONLY use actual facts from the documents (system names, technologies, data mentioned)
4. DO NOT make up information
5. DO NOT give generic advice like "consider" or "should implement"
6. If the documents don't contain relevant information, respond EXACTLY as:
   - "Not specified in documentation" OR
   - "No information about [topic] in documentation"

**RESPONSE STYLE GUIDE (illustrative examples only - DO NOT copy these answers):**

When docs contain specific info:
✅ Quote actual facts: "System uses [actual tech from docs] with [actual data from docs]"
❌ Generic advice: "Consider implementing best practices for security"

When docs lack specific info:
✅ Be honest: "Not specified in documentation"
❌ Make assumptions: "The system likely uses standard encryption"

When question asks about something not in docs:
✅ Say so clearly: "No information about patents in documentation"
❌ Provide generic guidance: "Consider consulting with your legal team"

**IMPORTANT:**
- DO NOT copy the illustrative examples above
- ANALYZE THE ACTUAL DOCUMENTS PROVIDED
- Use specific facts from the user's documents only

**ONE DEMONSTRATION (different domain to show format - DO NOT copy content):**
Example Question: "What programming language is used?"
Example Docs: "Mobile app built with React Native and TypeScript"
Example Response:
{{
    "has_suggestion": true,
    "technical_guidance": "React Native and TypeScript",
    "confidence": "high",
    "reasoning": "Stated in mobile app documentation",
    "supporting_context": ["Mobile app built with React Native and TypeScript"]
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  CRITICAL: NOW ANALYZE THE USER'S ACTUAL DOCUMENTS ABOVE ⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The documents you must analyze are listed in the "DOCUMENTS TO ANALYZE" section above.
Your answer MUST come from those documents ONLY - not from the examples.
Question to answer: "{rephrased_question}"

**OUTPUT FORMAT (JSON):**
{{
    "has_suggestion": true,
    "technical_guidance": "Your one-sentence answer using ONLY facts from the documents above",
    "confidence": "high/medium/low",
    "reasoning": "Which document(s) this came from OR 'No relevant information found'",
    "supporting_context": ["Actual quote 1 from docs", "Actual quote 2 from docs"] or []
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
    """
    Honest fallback when LLM cannot generate a suggestion.
    Returns 'Not specified in documentation' instead of generic advice.
    """
    logger.info(f"[FALLBACK] LLM could not generate suggestion for: {question_text[:100]}...")
    logger.info(f"[FALLBACK] Available documents: {len(document_summaries)}")

    # Extract topic from question to make the message more specific
    question_lower = question_text.lower()
    topic = "this information"

    if any(word in question_lower for word in ['patent', 'intellectual property', 'ip']):
        topic = "patent information"
    elif any(word in question_lower for word in ['vendor', 'supplier', 'third party']):
        topic = "vendor/supplier details"
    elif any(word in question_lower for word in ['backup', 'recovery', 'disaster']):
        topic = "backup/recovery information"
    elif any(word in question_lower for word in ['security', 'access', 'authentication']):
        topic = "security details"
    elif any(word in question_lower for word in ['data', 'privacy', 'personal information']):
        topic = "data/privacy information"
    elif any(word in question_lower for word in ['monitoring', 'logging']):
        topic = "monitoring details"

    return {
        "has_suggestion": True,
        "technical_guidance": f"No information about {topic} in documentation",
        "confidence": "low",
        "reasoning": "Could not find relevant information in uploaded documents",
        "supporting_context": []
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
