"""
DocuScan Configuration Module

This module provides comprehensive configuration management for the DocuScan
legal document classification system with environment variable support,
validation, and type safety.
"""

import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pathlib import Path


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="docuscan", description="Database name")
    user: str = Field(default="docuscan", description="Database user")
    password: str = Field(default="docuscan123", description="Database password")
    
    @property
    def url(self) -> str:
        """Generate database URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class ElasticsearchSettings(BaseSettings):
    """Elasticsearch configuration settings."""
    
    host: str = Field(default="localhost", description="Elasticsearch host")
    port: int = Field(default=9200, description="Elasticsearch port")
    index_name: str = Field(default="docuscan_documents", description="Main index name")
    max_retries: int = Field(default=3, description="Max connection retries")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    @property
    def url(self) -> str:
        """Generate Elasticsearch URL."""
        return f"http://{self.host}:{self.port}"
    
    @property
    def hosts(self) -> List[Dict[str, Any]]:
        """Generate hosts configuration."""
        return [{"host": self.host, "port": self.port}]


class OCRSettings(BaseSettings):
    """OCR processing configuration."""
    
    tesseract_cmd: Optional[str] = Field(default=None, description="Tesseract command path")
    languages: List[str] = Field(default=["eng"], description="OCR languages")
    psm: int = Field(default=6, description="Page segmentation mode")
    oem: int = Field(default=3, description="OCR engine mode")
    dpi: int = Field(default=300, description="Image DPI for OCR")
    
    @validator('languages')
    def validate_languages(cls, v):
        """Validate OCR languages."""
        valid_langs = ['eng', 'spa', 'fra', 'deu', 'ita', 'por']
        for lang in v:
            if lang not in valid_langs:
                raise ValueError(f"Unsupported language: {lang}")
        return v


class NLPSettings(BaseSettings):
    """NLP processing configuration."""
    
    spacy_model: str = Field(default="en_core_web_sm", description="spaCy model name")
    max_doc_length: int = Field(default=1000000, description="Maximum document length")
    batch_size: int = Field(default=32, description="Processing batch size")
    confidence_threshold: float = Field(default=0.7, description="Classification confidence threshold")
    
    # Legal document classification categories
    case_types: List[str] = Field(
        default=[
            "criminal", "civil", "corporate", "family", "immigration",
            "employment", "real_estate", "tax", "bankruptcy", "intellectual_property"
        ],
        description="Supported case types"
    )
    
    urgency_keywords: Dict[str, List[str]] = Field(
        default={
            "critical": ["urgent", "emergency", "immediate", "asap", "deadline today"],
            "high": ["priority", "important", "deadline", "time-sensitive"],
            "medium": ["review", "pending", "follow-up"],
            "low": ["routine", "standard", "when possible"]
        },
        description="Keywords for urgency classification"
    )


class FileUploadSettings(BaseSettings):
    """File upload configuration."""
    
    upload_dir: Path = Field(default=Path("uploads"), description="Upload directory")
    max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
    allowed_extensions: List[str] = Field(
        default=[".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg", ".tiff"],
        description="Allowed file extensions"
    )
    temp_dir: Path = Field(default=Path("temp"), description="Temporary files directory")
    
    def __post_init__(self):
        """Create directories if they don't exist."""
        self.upload_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)


class SecuritySettings(BaseSettings):
    """Security and authentication settings."""
    
    secret_key: str = Field(default="your_secret_key_here", description="JWT secret key")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Token expiration time")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration")
    
    # API Rate limiting
    rate_limit_per_minute: int = Field(default=100, description="API rate limit per minute")
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        """Validate secret key strength."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v


class APISettings(BaseSettings):
    """API configuration settings."""
    
    title: str = Field(default="DocuScan API", description="API title")
    version: str = Field(default="2.0.0", description="API version")
    description: str = Field(
        default="Professional Legal Document Classification and Management System",
        description="API description"
    )
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Debug mode")
    docs_url: str = Field(default="/docs", description="API documentation URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc documentation URL")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:80", "http://localhost:8080"],
        description="CORS allowed origins"
    )


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        description="Log format"
    )
    file_path: Optional[Path] = Field(default=Path("logs/docuscan.log"), description="Log file path")
    max_file_size: str = Field(default="10 MB", description="Maximum log file size")
    retention: str = Field(default="30 days", description="Log retention period")
    
    def __post_init__(self):
        """Create log directory if it doesn't exist."""
        if self.file_path:
            self.file_path.parent.mkdir(exist_ok=True)


class MonitoringSettings(BaseSettings):
    """System monitoring configuration."""
    
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=8001, description="Metrics endpoint port")
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    
    # System thresholds
    max_cpu_percent: float = Field(default=80.0, description="Maximum CPU usage percentage")
    max_memory_percent: float = Field(default=85.0, description="Maximum memory usage percentage")
    max_disk_percent: float = Field(default=90.0, description="Maximum disk usage percentage")


class DocuScanSettings(BaseSettings):
    """Main DocuScan application settings."""
    
    # Environment
    environment: str = Field(default="development", description="Environment name")
    
    # Sub-configurations
    api: APISettings = Field(default_factory=APISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    elasticsearch: ElasticsearchSettings = Field(default_factory=ElasticsearchSettings)
    ocr: OCRSettings = Field(default_factory=OCRSettings)
    nlp: NLPSettings = Field(default_factory=NLPSettings)
    file_upload: FileUploadSettings = Field(default_factory=FileUploadSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment value."""
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


# Global settings instance
settings = DocuScanSettings()

# Ensure upload and log directories exist
os.makedirs(settings.file_upload.upload_dir, exist_ok=True)
os.makedirs(os.path.dirname(settings.logging.file_path) if settings.logging.file_path else "", exist_ok=True) 