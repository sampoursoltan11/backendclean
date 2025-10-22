"""
Configuration settings for TRA system - Simplified version without SES
"""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    # AWS Configuration
    aws_region: str = "ap-southeast-2"
    aws_default_region: str = "ap-southeast-2"  # Added for compatibility with AWS_DEFAULT_REGION
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Deployment Configuration
    ecr_repository_name: Optional[str] = "tra-system"
    cluster_name: Optional[str] = "tra-cluster"
    service_name: Optional[str] = "tra-service"
    
    # DynamoDB Configuration
    dynamodb_table_name: str = "tra-system"
    dynamodb_region: str = "ap-southeast-2"
    
    # S3 Configuration
    s3_bucket_name: str = "bhp-tra-agent-docs-poc"
    s3_region: str = "ap-southeast-2"
    
    # Bedrock Configuration
    bedrock_region: str = "ap-southeast-2"
    # Model: Claude 3 Haiku - more readily available without inference profile requirements
    # Using Haiku for better availability and lower cost
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    # Fast model for document summarization (same as main for now, can be changed)
    bedrock_summary_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    # Embeddings: Titan Text Embeddings V2
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v2:0"
    bedrock_knowledge_base_id: Optional[str] = None
    bedrock_data_source_id: Optional[str] = None
    bedrock_execution_role_arn: Optional[str] = None
    
    # Application Configuration
    api_title: str = "TRA System API"
    api_version: str = "1.0.0"
    api_description: str = "Technology Risk Assessment System - Simplified Version"
    
    # File and Directory Configuration
    decision_tree_config_path: str = "backend/config/decision_tree2.yaml"
    session_storage_dir: str = "./sessions"
    local_kb_dir: str = "backend/local_kb"
    local_s3_dir: str = "backend/local_s3"
    s3_session_prefix: str = "sessions"
    
    # Development and Testing Configuration
    test_server_url: str = "http://localhost:8000"
    
    # Security
    jwt_secret_key: str = "your-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Static Links Configuration
    base_url: str = "http://localhost:8000"
    assessor_base_url: str = "http://localhost:8000"
    
    # WebSocket Configuration
    websocket_url: str = "wss://tra-system.company.com/ws"
    
    # CORS Configuration
    cors_origins: list = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def converse_model_id(self) -> str:
        """Return a Bedrock Converse-friendly model id derived from configured value."""
        try:
            from backend.utils.aws_utils import get_converse_model_id
            model_id = get_converse_model_id(self.bedrock_model_id, self.bedrock_region)
            return model_id
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error converting model ID: {e}")
            return self.bedrock_model_id


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings (useful for testing)."""
    global _settings
    _settings = Settings()
    return _settings
