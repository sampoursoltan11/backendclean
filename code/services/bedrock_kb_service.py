"""Bedrock Knowledge Base service with optional AWS Bedrock integration.

When AWS is configured, this attempts to use Bedrock APIs (best-effort). If
not configured or Bedrock calls fail, it falls back to a local document store
under `backend/local_kb/` and a naive substring search for retrieval.

Implemented methods:
- upload_document_to_kb(file_content, filename, session_id)
- retrieve_and_generate(query, session_id, context)
- retrieve_only(query, max_results)
- get_knowledge_base_status()
- health_check()
"""

import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import aioboto3
import boto3  # Expose boto3 at module scope for tests that patch backend.services.bedrock_kb_service.boto3
from backend.core.config import get_settings
from backend.utils.hybrid_async import HybridAsyncDict

# Use configurable local directory
settings = get_settings()
BASE = Path(settings.local_kb_dir)
BASE.mkdir(parents=True, exist_ok=True)

class BedrockKnowledgeBaseService:

    async def list_all_kb_items(self) -> list:
        """List all documents/items in the Bedrock Knowledge Base (global KB listing)."""
        # If AWS Bedrock is enabled, try to list documents via Bedrock API
        print(f"[KB DEBUG] list_all_kb_items: use_aws={self._use_aws}, kb_id={self.knowledge_base_id}, data_source_id={getattr(self.settings, 'bedrock_data_source_id', None)}")
        if self._use_aws and self.knowledge_base_id and self.settings.bedrock_data_source_id:
            try:
                session = aioboto3.Session()
                async with session.client('bedrock-agent', region_name=self.region) as client:
                    paginator = client.get_paginator('list_knowledge_base_documents')
                    items = []
                    async for page in paginator.paginate(
                        knowledgeBaseId=self.knowledge_base_id,
                        dataSourceId=self.settings.bedrock_data_source_id
                    ):
                        print(f"[KB DEBUG] Bedrock paginator page: {page}")
                        for doc in page.get('documentDetails', []):
                            print(f"[KB DEBUG] Bedrock doc detail: {doc}")
                            items.append({
                                'document_id': doc.get('identifier', {}).get('s3', {}).get('uri', ''),
                                'filename': doc.get('identifier', {}).get('s3', {}).get('uri', '').split('/')[-1],
                                'status': doc.get('status'),
                                's3_key': doc.get('identifier', {}).get('s3', {}).get('uri', ''),
                                'updated_at': doc.get('updatedAt'),
                                'source': doc.get('identifier', {}).get('dataSourceType', ''),
                            })
                    print(f"[KB DEBUG] Bedrock KB items found: {len(items)}")
                    return items
            except Exception as e:
                print(f"[KB DEBUG] Bedrock list_all_kb_items failed: {e}")
                # fall through to S3/local fallback
        # Fallback: list from S3 (if configured) or local directory
        # Try S3
        try:
            from backend.services.s3_service import S3Service
            s3_service = S3Service()
            bucket = self.settings.s3_bucket
            prefix = 'knowledge-base/'
            s3_files = await s3_service.list_files(bucket, prefix)
            items = []
            for f in s3_files:
                items.append({
                    'document_id': f,
                    'filename': f.split('/')[-1],
                    'status': 'UNKNOWN',
                    's3_key': f,
                    'updated_at': '',
                    'source': 'S3',
                })
            if items:
                return items
        except Exception as e:
            print(f"[KB DEBUG] S3 list_all_kb_items failed: {e}")
        # Fallback: local directory scan
        items = []
        for assessment_dir in self.kb_path.glob('*'):
            if assessment_dir.is_dir():
                for f in assessment_dir.glob('**/*'):
                    if f.is_file():
                        items.append({
                            'document_id': str(f),
                            'filename': f.name,
                            'status': 'LOCAL',
                            's3_key': '',
                            'updated_at': '',
                            'source': 'local',
                        })
        return items
    def __init__(self):
        from backend.core.config import get_settings

        self.settings = get_settings()
        self.kb_path = BASE
        # Detect AWS usage
        self._use_aws = bool(os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('AWS_PROFILE') or os.getenv('AWS_DEFAULT_REGION') or self.settings.bedrock_region)
        print(f"[DEBUG] BedrockKnowledgeBaseService initialized. Use AWS: {self._use_aws} (env_creds={bool(os.getenv('AWS_ACCESS_KEY_ID'))}, env_profile={bool(os.getenv('AWS_PROFILE'))}, env_region={bool(os.getenv('AWS_DEFAULT_REGION'))}, config_region={bool(self.settings.bedrock_region)})")
        self.bedrock_model_id = self.settings.bedrock_model_id
        self.region = self.settings.bedrock_region
        self.knowledge_base_id = self.settings.bedrock_knowledge_base_id
        
        # Extract account ID from execution role ARN
        self.account_id = None
        if self.settings.bedrock_execution_role_arn:
            # ARN format: arn:aws:iam::448608816491:role/tra-bedrock-execution-role
            arn_parts = self.settings.bedrock_execution_role_arn.split(':')
            if len(arn_parts) >= 5:
                self.account_id = arn_parts[4]

    def health_check(self) -> Dict[str, Any]:
        async def _async():
            if not self._use_aws:
                return {"success": True, "message": "local KB available", "path": str(self.kb_path)}
            try:
                if self.knowledge_base_id:
                    session = aioboto3.Session()
                    async with session.client('bedrock-agent', region_name=self.region) as client:
                        resp = await client.get_knowledge_base(knowledgeBaseId=self.knowledge_base_id)
                        return {"success": True, "message": "bedrock KB available", "kb_id": self.knowledge_base_id, "status": resp.get("status")}
                else:
                    return {"success": True, "message": "bedrock configured but no KB ID", "path": str(self.kb_path)}
            except Exception as e:
                return {"success": False, "error": str(e), "path": str(self.kb_path)}

        def _sync():
            return {"status": "healthy"}

        return HybridAsyncDict(_sync, _async)


    def upload_document_to_kb(self, file_content: bytes, filename: str, assessment_id: str) -> Dict[str, Any]:
        """Upload document to Knowledge Base with enhanced ingestion monitoring (TRA-centric)."""
        print(f"[KB DEBUG] upload_document_to_kb called: filename={filename}, assessment_id={assessment_id}, file_size={len(file_content)}")
        async def _async():
            # Always save locally first
            sdir = self.kb_path.joinpath(assessment_id)
            sdir.mkdir(parents=True, exist_ok=True)
            dest = sdir.joinpath(filename)
            with open(dest, 'wb') as f:
                f.write(file_content)
            print(f"[KB DEBUG] Saved file locally at {dest}")
            result = {
                "document_id": f"local-{assessment_id}-{filename}",
                "status": "processing",
                "s3_key": str(dest),
                "uploaded_at": datetime.utcnow().isoformat(),
                "local_path": str(dest)
            }
            if self._use_aws and self.knowledge_base_id and self.settings.bedrock_data_source_id:
                try:
                        from backend.services.s3_service import S3Service
                        s3_service = S3Service()
                        s3_key = f"knowledge-base/{assessment_id}/{filename}"
                        s3_result = await s3_service.upload_file(file_content, s3_key)
                        print(f"[KB DEBUG] S3 upload result: {s3_result}")
                        if s3_result.get('success'):
                            result['s3_uploaded'] = True
                            result['s3_key'] = s3_key
                            result['s3_bucket'] = s3_result.get('bucket')
                            session = aioboto3.Session()
                            async with session.client('bedrock-agent', region_name=self.region) as client:
                                resp = await client.start_ingestion_job(
                                    knowledgeBaseId=self.knowledge_base_id,
                                    dataSourceId=self.settings.bedrock_data_source_id,
                                    description=f"Ingestion for {filename} in assessment {assessment_id}"
                                )
                                ingestion_job_id = resp.get('ingestionJob', {}).get('ingestionJobId')
                                print(f"[KB DEBUG] Bedrock ingestion started: job_id={ingestion_job_id}")
                                result['ingestion_job_id'] = ingestion_job_id
                                result['bedrock_ingestion_started'] = True
                                result['status'] = 'ingesting'
                except Exception as e:
                    print(f"[KB DEBUG] Bedrock ingestion failed: {e}")
                    result['bedrock_error'] = f"Bedrock ingestion failed: {e}"
                    result['status'] = 'local_only'
            print(f"[KB DEBUG] upload_document_to_kb result: {result}")
            return result

        def _sync():
            return {"document_id": f"local-{session_id}-{filename}", "status": "processing"}

        return HybridAsyncDict(_sync, _async)
    
    async def check_ingestion_status(self, ingestion_job_id: str) -> Dict[str, Any]:
        """Check the status of a Bedrock Knowledge Base ingestion job."""
        if not self._use_aws or not self.knowledge_base_id:
            return {"success": False, "error": "AWS Bedrock not configured"}
        
        try:
            session = aioboto3.Session()
            async with session.client('bedrock-agent', region_name=self.region) as client:
                resp = await client.get_ingestion_job(
                    knowledgeBaseId=self.knowledge_base_id,
                    dataSourceId=self.settings.bedrock_data_source_id,
                    ingestionJobId=ingestion_job_id
                )
                
                job = resp.get('ingestionJob', {})
                status = job.get('status', 'UNKNOWN')
                
                return {
                    "success": True,
                    "status": status,
                    "job_id": ingestion_job_id,
                    "started_at": job.get('startedAt'),
                    "updated_at": job.get('updatedAt'),
                    "documents_scanned": job.get('statistics', {}).get('numberOfDocumentsScanned', 0),
                    "documents_indexed": job.get('statistics', {}).get('numberOfDocumentsIndexed', 0),
                    "is_complete": status in ['COMPLETE', 'FAILED'],
                    "is_ready": status == 'COMPLETE'
                }
                
        except Exception as e:
            return {"success": False, "error": f"Failed to check ingestion status: {e}"}
    
    async def wait_for_ingestion(self, ingestion_job_id: str, max_wait_seconds: int = 60) -> Dict[str, Any]:
        """Wait for ingestion job to complete (with timeout)."""
        import asyncio
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            status_result = await self.check_ingestion_status(ingestion_job_id)
            
            if not status_result.get("success"):
                return status_result
            
            if status_result.get("is_complete"):
                return status_result
            
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait_seconds:
                return {
                    "success": True,
                    "status": "TIMEOUT",
                    "message": f"Ingestion still in progress after {max_wait_seconds} seconds",
                    "elapsed_seconds": elapsed
                }
            
            # Wait before checking again
            await asyncio.sleep(2)
    
    async def test_document_availability(self, filename: str, session_id: str) -> Dict[str, Any]:
        """Test if a specific document is available and queryable in the Knowledge Base."""
        try:
            # Try to query for the specific document
            test_query = f"What information is available in the document {filename}? Summarize the main content."
            
            result = await self.retrieve_and_generate(test_query, session_id)
            
            # Check if the response references the specific document
            response_text = result.get('response', '').lower()
            filename_mentioned = filename.lower() in response_text
            has_meaningful_content = len(response_text.strip()) > 50
            
            return {
                "success": True,
                "document_available": filename_mentioned and has_meaningful_content,
                "filename": filename,
                "session_id": session_id,
                "test_response": result.get('response', ''),
                "confidence": result.get('confidence', 0.0)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Document availability test failed: {e}",
                "document_available": False
            }

    async def retrieve_and_generate(self, query: str, assessment_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        print(f"[KB DEBUG] retrieve_and_generate called: query={query!r}, assessment_id={assessment_id}")
        # If AWS Bedrock RetrieveAndGenerate is available, prefer that
        if self._use_aws:
            try:
                session = aioboto3.Session()
                async with session.client('bedrock-agent-runtime', region_name=self.region) as client:
                    # Use the proper Bedrock Agent Runtime API
                    if self.knowledge_base_id:
                        resp = await client.retrieve_and_generate(
                            input={'text': query},
                            retrieveAndGenerateConfiguration={
                                'type': 'KNOWLEDGE_BASE',
                                'knowledgeBaseConfiguration': {
                                    'knowledgeBaseId': self.knowledge_base_id,
                                    'modelArn': f'arn:aws:bedrock:{self.region}::foundation-model/{self.bedrock_model_id}'
                                }
                            }
                        )
                        print(f"[KB DEBUG] Bedrock retrieve_and_generate response: {resp}")
                        return {
                            'response': resp.get('output', {}).get('text', ''),
                            'citations': resp.get('citations', []),
                            'assessment_id': assessment_id,
                            'confidence': 0.8
                        }
            except Exception as e:
                print(f"[KB DEBUG] Bedrock retrieve_and_generate failed: {e}")
                # fall through to local retrieval

        # Local fallback: naive substring search in assessment folder
        assessment_dir = self.kb_path.joinpath(assessment_id)
        print(f"[KB DEBUG] Local KB search in: {assessment_dir}")
        results = []
        if assessment_dir.exists():
            for f in assessment_dir.glob('**/*'):
                if f.is_file():
                    try:
                        text = f.read_text(encoding='utf-8', errors='ignore')
                        if query.lower() in text.lower():
                            results.append({
                                "filename": f.name,
                                "path": str(f),
                                "snippet": text[:400]
                            })
                    except Exception as e:
                        print(f"[KB DEBUG] Error reading {f}: {e}")
                        continue
        response_text = "".join([r['snippet'] for r in results]) or f"No local KB matches for '{query}'"
        print(f"[KB DEBUG] Local KB search results: {results}")
        return {
            "response": response_text,
            "citations": results[:5],
            "assessment_id": assessment_id,
            "confidence": 0.5 if results else 0.0
        }

    async def retrieve_only(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        # For AWS-enabled mode this would call Bedrock search; fallback to local search
        matches = []
        for f in self.kb_path.glob('**/*'):
            if f.is_file():
                try:
                    text = f.read_text(encoding='utf-8', errors='ignore')
                    if query.lower() in text.lower():
                        matches.append({"filename": f.name, "path": str(f)})
                        if len(matches) >= max_results:
                            break
                except Exception:
                    continue
        return {"results": matches}

    async def get_knowledge_base_status(self) -> Dict[str, Any]:
        return {"success": True, "indexed_sessions": len([p for p in self.kb_path.iterdir() if p.is_dir()])}
