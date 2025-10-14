"""
Enhanced File Tracking Service for TRA System

Provides comprehensive file management with:
- Human-readable file identifiers
- Project-based organization
- Context-aware file linking
- Automatic agent context detection
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import hashlib
import re

from backend.models.tra_models import DocumentMetadata
from backend.services.dynamodb_service import DynamoDBService


class FileTrackingService:
    """Enhanced file tracking with intelligent naming and context detection."""
    
    def __init__(self):
        self.db_service = DynamoDBService()
        
    def generate_file_id(self, filename: str, session_id: str = None, project_name: str = None) -> str:
        """Generate human-readable file ID."""
        # Clean filename for ID generation
        clean_name = re.sub(r'[^\w\s-]', '', filename.lower())
        clean_name = re.sub(r'[-\s]+', '-', clean_name)
        
        # Extract project hint from filename or use session
        project_hint = self._extract_project_hint(filename, project_name)
        
        # Generate short unique suffix
        timestamp = datetime.now().strftime("%Y%m%d")
        hash_suffix = hashlib.md5(f"{filename}{session_id}{datetime.now().isoformat()}".encode()).hexdigest()[:6]
        
        return f"{project_hint}-{clean_name}-{timestamp}-{hash_suffix}"
    
    def _extract_project_hint(self, filename: str, project_name: str = None) -> str:
        """Extract project identifier from filename or project name."""
        if project_name:
            clean_project = re.sub(r'[^\w\s]', '', project_name.lower())
            clean_project = re.sub(r'\s+', '-', clean_project)[:15]
            return clean_project
            
        # Try to extract from filename
        filename_lower = filename.lower()
        
        # Common project indicators
        if 'techcorp' in filename_lower:
            return 'techcorp'
        elif 'project' in filename_lower and 'summary' in filename_lower:
            return 'proj-summary'
        elif 'migration' in filename_lower:
            return 'migration'
        elif 'assessment' in filename_lower:
            return 'assessment'
        elif 'proposal' in filename_lower:
            return 'proposal'
        else:
            return 'general'
    
    def create_enhanced_s3_key(self, file_id: str, filename: str, project_hint: str = None) -> str:
        """Create organized S3 key structure."""
        # Use project-based organization instead of random sessions
        project = project_hint or self._extract_project_hint(filename)
        date_folder = datetime.now().strftime("%Y/%m")
        
        # Clean filename for storage
        safe_filename = re.sub(r'[^\w\s.-]', '', filename)
        safe_filename = re.sub(r'\s+', '_', safe_filename)
        
        return f"documents/{project}/{date_folder}/{file_id}/{safe_filename}"
    
    async def create_file_metadata(self, 
                                 filename: str, 
                                 file_content: bytes,
                                 session_id: str,
                                 assessment_id: str,
                                 project_name: str = None,
                                 tags: List[str] = None) -> Dict[str, Any]:
        """Create comprehensive file metadata, now requiring assessment_id (TRA)."""
        # Generate enhanced identifiers
        file_id = self.generate_file_id(filename, assessment_id, project_name)
        s3_key = self.create_enhanced_s3_key(file_id, filename, project_name)
        # Extract content insights
        content_insights = self._analyze_content(file_content, filename)
        # Create metadata record
        metadata = DocumentMetadata(
            document_id=file_id,
            session_id=session_id,
            filename=filename,
            file_size=len(file_content),
            content_type=self._get_content_type(filename),
            s3_key=s3_key,
            s3_bucket=None,  # Will be set by S3 service
            assessment_id=assessment_id,
            pk=f"DOC#{file_id}",
            sk=f"METADATA#{file_id}",
            # Enhanced metadata
            project_name=project_name,
            file_category=content_insights.get('category', 'document'),
            content_summary=content_insights.get('summary', ''),
            tags=tags or [],
            upload_context={
                'session_id': session_id,
                'assessment_id': assessment_id,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'user_agent': 'TRA-System',
                'file_hash': hashlib.sha256(file_content).hexdigest()
            }
        )
        return {
            'file_id': file_id,
            's3_key': s3_key,
            'metadata': metadata,
            'content_insights': content_insights
        }
    
    def _analyze_content(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Analyze file content for categorization and context."""
        insights = {
            'category': 'document',
            'summary': '',
            'detected_content_type': '',
            'context_hints': []
        }
        
        filename_lower = filename.lower()
        
        # Categorize by filename
        if any(ext in filename_lower for ext in ['.pdf', '.doc', '.docx']):
            insights['category'] = 'document'
            insights['detected_content_type'] = 'text_document'
        elif any(ext in filename_lower for ext in ['.xls', '.xlsx', '.csv']):
            insights['category'] = 'spreadsheet'
            insights['detected_content_type'] = 'data_sheet'
        elif any(ext in filename_lower for ext in ['.ppt', '.pptx']):
            insights['category'] = 'presentation'
            insights['detected_content_type'] = 'slide_deck'
        
        # Extract context hints from filename
        context_keywords = {
            'financial': ['budget', 'cost', 'financial', 'revenue', 'expense'],
            'technical': ['technical', 'system', 'architecture', 'infrastructure'],
            'project': ['project', 'proposal', 'plan', 'roadmap'],
            'assessment': ['assessment', 'evaluation', 'review', 'analysis'],
            'migration': ['migration', 'transition', 'move', 'upgrade'],
            'compliance': ['compliance', 'audit', 'regulatory', 'policy'],
            'risk': ['risk', 'security', 'threat', 'vulnerability']
        }
        
        for category, keywords in context_keywords.items():
            if any(keyword in filename_lower for keyword in keywords):
                insights['context_hints'].append(category)
        
        # Generate summary based on filename and context
        if insights['context_hints']:
            insights['summary'] = f"Document related to {', '.join(insights['context_hints'][:3])}"
        else:
            insights['summary'] = f"General {insights['category']} file"
        
        return insights
    
    def _get_content_type(self, filename: str) -> str:
        """Determine MIME type from filename."""
        ext = Path(filename).suffix.lower()
        
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.txt': 'text/plain',
            '.csv': 'text/csv'
        }
        
        return content_types.get(ext, 'application/octet-stream')
    
    async def get_assessment_files(self, assessment_id: str) -> List[Dict[str, Any]]:
        """Get all files associated with an assessment (TRA)."""
        try:
            # Use DynamoDBService methods instead of direct table access
            if self.db_service._use_aws:
                import aioboto3
                session = aioboto3.Session()
                async with session.client('dynamodb') as client:
                    response = await client.scan(
                        TableName=self.db_service.table_name,
                        FilterExpression='assessment_id = :assessment_id AND begins_with(pk, :doc_prefix)',
                        ExpressionAttributeValues={
                            ':assessment_id': {'S': assessment_id},
                            ':doc_prefix': {'S': 'DOC#'}
                        }
                    )
                    files = []
                    for item in response.get('Items', []):
                        # Convert DynamoDB item format to regular dict
                        file_data = {}
                        for key, value in item.items():
                            if 'S' in value:
                                file_data[key] = value['S']
                            elif 'N' in value:
                                file_data[key] = value['N']
                            elif 'L' in value:
                                file_data[key] = [v.get('S', '') for v in value['L']]
                        if file_data.get('pk', '').startswith('DOC#'):
                            files.append({
                                'file_id': file_data.get('document_id', ''),
                                'filename': file_data.get('filename', ''),
                                'category': file_data.get('file_category', 'document'),
                                'summary': file_data.get('content_summary', ''),
                                'tags': file_data.get('tags', []),
                                'upload_time': file_data.get('created_at', ''),
                                's3_key': file_data.get('s3_key', '')
                            })
                    return files
            else:
                # Fallback: use local directory scan
                return await self._get_assessment_files_fallback(assessment_id)
        except Exception as e:
            logger.error(f"Error getting assessment files: {e}")
            # Fallback to directory scan
            return await self._get_assessment_files_fallback(assessment_id)
    
    async def _get_session_files_fallback(self, session_id: str) -> List[Dict[str, Any]]:
        """Fallback method to get files from local directory."""
        try:
            from pathlib import Path
            from backend.core.config import get_settings
            
            settings = get_settings()
            # Check both session formats
            session_dirs = [
                Path(settings.local_kb_dir) / session_id,
                Path(settings.local_kb_dir) / f'session_{session_id}'
            ]
            
            files = []
            for session_dir in session_dirs:
                if session_dir.exists():
                    for file_path in session_dir.glob('*'):
                        if file_path.is_file():
                            insights = self._analyze_content(b'', file_path.name)
                            files.append({
                                'file_id': f'local-{session_id}-{file_path.name}',
                                'filename': file_path.name,
                                'category': insights['category'],
                                'summary': insights['summary'],
                                'tags': insights['context_hints'],
                                'upload_time': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                                's3_key': f'knowledge-base/{session_id}/{file_path.name}'
                            })
                    break  # Found files in one of the directories
            
            return files
        except Exception as e:
            logger.error(f"Error in fallback file listing: {e}")
            return []
    
    async def get_project_files(self, project_name: str) -> List[Dict[str, Any]]:
        """Get all files associated with a project."""
        try:
            if self.db_service._use_aws:
                import aioboto3
                session = aioboto3.Session()
                async with session.client('dynamodb') as client:
                    response = await client.scan(
                        TableName=self.db_service.table_name,
                        FilterExpression='project_name = :project AND begins_with(pk, :doc_prefix)',
                        ExpressionAttributeValues={
                            ':project': {'S': project_name},
                            ':doc_prefix': {'S': 'DOC#'}
                        }
                    )
                    
                    files = []
                    for item in response.get('Items', []):
                        # Convert DynamoDB item format to regular dict
                        file_data = {}
                        for key, value in item.items():
                            if 'S' in value:
                                file_data[key] = value['S']
                            elif 'N' in value:
                                file_data[key] = value['N']
                            elif 'L' in value:
                                file_data[key] = [v.get('S', '') for v in value['L']]
                        
                        if file_data.get('pk', '').startswith('DOC#'):
                            files.append({
                                'file_id': file_data.get('document_id', ''),
                                'filename': file_data.get('filename', ''),
                                'category': file_data.get('file_category', 'document'),
                                'summary': file_data.get('content_summary', ''),
                                'tags': file_data.get('tags', []),
                                'upload_time': file_data.get('created_at', ''),
                                's3_key': file_data.get('s3_key', '')
                            })
                    
                    return files
            else:
                # In-memory fallback doesn't support project filtering easily
                return []
                
        except Exception as e:
            logger.error(f"Error getting project files: {e}")
            return []
    
    async def link_file_to_assessment(self, file_id: str, assessment_id: str) -> bool:
        """Link a file to a specific assessment."""
        try:
            if self.db_service._use_aws:
                import aioboto3
                session = aioboto3.Session()
                async with session.client('dynamodb') as client:
                    await client.update_item(
                        TableName=self.db_service.table_name,
                        Key={
                            'pk': {'S': f"DOC#{file_id}"},
                            'sk': {'S': f"METADATA#{file_id}"}
                        },
                        UpdateExpression='SET assessment_id = :assessment_id, gsi1_pk = :gsi1_pk, gsi1_sk = :gsi1_sk',
                        ExpressionAttributeValues={
                            ':assessment_id': {'S': assessment_id},
                            ':gsi1_pk': {'S': f"ASSESSMENT#{assessment_id}"},
                            ':gsi1_sk': {'S': f"DOC#{file_id}"}
                        }
                    )
                return True
            else:
                # For in-memory fallback, we can't easily update records
                logger.debug(f"Linking file {file_id} to assessment {assessment_id} (in-memory mode)")
                return True
                
        except Exception as e:
            logger.error(f"Error linking file to assessment: {e}")
            return False
    
    def get_context_for_agent(self, session_id: str, recent_files_only: bool = True) -> str:
        """Generate context string for AI agent about available files."""
        # This will be used by the agent to understand what files are available
        # Implementation will be added when integrating with the agent
        return f"Session {session_id} file context will be generated here"