"""
DocuScan Production Configuration

Comprehensive configuration for the production-ready DocuScan system
with OCR, NLP, authentication, and all required services.
"""

import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from pathlib import Path


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    name: str = Field(default="docuscan", env="DB_NAME")
    user: str = Field(default="docuscan", env="DB_USER")
    password: str = Field(default="docuscan123", env="DB_PASSWORD")
    
    @property
    def url(self) -> str:
        """Generate database URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class ElasticsearchSettings(BaseSettings):
    """Elasticsearch configuration settings."""
    
    host: str = Field(default="localhost", env="ELASTICSEARCH_HOST")
    port: int = Field(default=9200, env="ELASTICSEARCH_PORT")
    url: str = Field(default="http://localhost:9200", env="ELASTICSEARCH_URL")
    index_name: str = Field(default="docuscan_documents", env="ELASTICSEARCH_INDEX")
    max_retries: int = Field(default=3, env="ELASTICSEARCH_MAX_RETRIES")
    timeout: int = Field(default=30, env="ELASTICSEARCH_TIMEOUT")
    
    @property
    def hosts(self) -> List[Dict[str, Any]]:
        """Generate hosts configuration."""
        return [{"host": self.host, "port": self.port}]


class RedisSettings(BaseSettings):
    """Redis configuration for caching and session management."""
    
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    @property
    def connection_url(self) -> str:
        """Generate Redis connection URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class OCRSettings(BaseSettings):
    """OCR processing configuration with Tesseract."""
    
    tesseract_cmd: str = Field(default="/usr/bin/tesseract", env="TESSERACT_CMD")
    languages: List[str] = Field(default=["eng"], env="OCR_LANGUAGES")
    psm: int = Field(default=6, env="OCR_PSM")  # Page segmentation mode
    oem: int = Field(default=3, env="OCR_OEM")  # OCR engine mode
    dpi: int = Field(default=300, env="OCR_DPI")
    timeout: int = Field(default=60, env="OCR_TIMEOUT")
    confidence_threshold: float = Field(default=0.6, env="OCR_CONFIDENCE_THRESHOLD")
    
    @validator('languages')
    def validate_languages(cls, v):
        """Validate OCR languages."""
        valid_langs = ['eng', 'spa', 'fra', 'deu', 'ita', 'por', 'chi_sim', 'chi_tra']
        for lang in v:
            if lang not in valid_langs:
                raise ValueError(f"Unsupported language: {lang}")
        return v


class NLPSettings(BaseSettings):
    """NLP processing configuration with spaCy and transformers."""
    
    spacy_model: str = Field(default="en_core_web_sm", env="SPACY_MODEL")
    max_doc_length: int = Field(default=1000000, env="NLP_MAX_DOC_LENGTH")
    batch_size: int = Field(default=32, env="NLP_BATCH_SIZE")
    confidence_threshold: float = Field(default=0.7, env="NLP_CONFIDENCE_THRESHOLD")
    
    # Legal document classification categories
    case_types: List[str] = Field(default=[
        "criminal", "civil", "corporate", "family", "immigration",
        "employment", "real_estate", "tax", "bankruptcy", "intellectual_property",
        "contract", "litigation", "regulatory", "compliance", "mergers_acquisitions"
    ])
    
    urgency_keywords: Dict[str, List[str]] = Field(default={
        "critical": [
            "urgent", "emergency", "immediate", "asap", "deadline today",
            "time-sensitive", "rush", "expedite", "crisis", "critical deadline"
        ],
        "high": [
            "priority", "important", "deadline", "time-sensitive", "soon",
            "upcoming deadline", "high priority", "needs attention", "follow up"
        ],
        "medium": [
            "review", "pending", "follow-up", "scheduled", "routine review",
            "standard processing", "normal priority"
        ],
        "low": [
            "routine", "standard", "when possible", "low priority", "reference",
            "archive", "informational", "fyi"
        ]
    })
    
    # Entity extraction settings
    entity_types: List[str] = Field(default=[
        "PERSON", "ORG", "MONEY", "DATE", "GPE", "LAW", "EVENT", "PRODUCT"
    ])


class FileUploadSettings(BaseSettings):
    """File upload and processing configuration."""
    
    upload_dir: Path = Field(default=Path("uploads"), env="UPLOAD_DIR")
    temp_dir: Path = Field(default=Path("temp"), env="TEMP_DIR")
    demo_data_dir: Path = Field(default=Path("demo_data"), env="DEMO_DATA_DIR")
    max_file_size_mb: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    
    allowed_extensions: List[str] = Field(default=[
        ".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg", 
        ".tiff", ".bmp", ".gif", ".xlsx", ".pptx"
    ])
    
    # File retention settings
    auto_delete_temp_files: bool = Field(default=True, env="AUTO_DELETE_TEMP")
    temp_file_retention_hours: int = Field(default=24, env="TEMP_RETENTION_HOURS")
    demo_data_retention_days: int = Field(default=30, env="DEMO_RETENTION_DAYS")
    
    def __post_init__(self):
        """Create directories if they don't exist."""
        for directory in [self.upload_dir, self.temp_dir, self.demo_data_dir]:
            directory.mkdir(exist_ok=True, parents=True)


class SecuritySettings(BaseSettings):
    """Security and authentication settings."""
    
    secret_key: str = Field(default="your-super-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, env="ACCESS_TOKEN_EXPIRE")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE")
    
    # API Rate limiting
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    max_upload_rate_mb_per_min: int = Field(default=50, env="MAX_UPLOAD_RATE_MB")
    
    # Password requirements
    min_password_length: int = Field(default=8, env="MIN_PASSWORD_LENGTH")
    require_special_chars: bool = Field(default=True, env="REQUIRE_SPECIAL_CHARS")
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        """Validate secret key strength."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v


class APISettings(BaseSettings):
    """API configuration settings."""
    
    title: str = Field(default="DocuScan API", env="API_TITLE")
    version: str = Field(default="2.0.0", env="API_VERSION")
    description: str = Field(default="Production Legal Document Classification System")
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="API_DEBUG")
    docs_url: str = Field(default="/docs", env="API_DOCS_URL")
    redoc_url: str = Field(default="/redoc", env="API_REDOC_URL")
    
    # CORS settings
    cors_origins: List[str] = Field(default=[
        "http://localhost:3000", "http://localhost:80", "http://localhost:8080",
        "http://127.0.0.1:3000", "https://localhost:3000"
    ], env="CORS_ORIGINS")
    
    # Request limits
    max_request_size_mb: int = Field(default=100, env="MAX_REQUEST_SIZE_MB")
    request_timeout_seconds: int = Field(default=300, env="REQUEST_TIMEOUT")


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}")
    file_path: Optional[Path] = Field(default=Path("logs/docuscan.log"), env="LOG_FILE_PATH")
    max_file_size: str = Field(default="10 MB", env="LOG_MAX_FILE_SIZE")
    retention: str = Field(default="30 days", env="LOG_RETENTION")
    
    # Structured logging
    json_format: bool = Field(default=True, env="LOG_JSON_FORMAT")
    include_request_id: bool = Field(default=True, env="LOG_INCLUDE_REQUEST_ID")
    
    def __post_init__(self):
        """Create log directory if it doesn't exist."""
        if self.file_path:
            self.file_path.parent.mkdir(exist_ok=True, parents=True)


class MonitoringSettings(BaseSettings):
    """System monitoring and health check configuration."""
    
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8001, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # System thresholds
    max_cpu_percent: float = Field(default=80.0, env="MAX_CPU_PERCENT")
    max_memory_percent: float = Field(default=85.0, env="MAX_MEMORY_PERCENT")
    max_disk_percent: float = Field(default=90.0, env="MAX_DISK_PERCENT")
    
    # Service monitoring
    monitor_elasticsearch: bool = Field(default=True, env="MONITOR_ELASTICSEARCH")
    monitor_redis: bool = Field(default=True, env="MONITOR_REDIS")
    monitor_ocr_queue: bool = Field(default=True, env="MONITOR_OCR_QUEUE")


class MLSettings(BaseSettings):
    """Machine Learning and AI configuration."""
    
    # Document summarization
    enable_summarization: bool = Field(default=True, env="ENABLE_SUMMARIZATION")
    max_summary_length: int = Field(default=300, env="MAX_SUMMARY_LENGTH")
    min_summary_length: int = Field(default=50, env="MIN_SUMMARY_LENGTH")
    
    # Classification confidence
    min_classification_confidence: float = Field(default=0.7, env="MIN_CLASSIFICATION_CONFIDENCE")
    use_transformer_classification: bool = Field(default=True, env="USE_TRANSFORMER_CLASSIFICATION")
    
    # Processing settings
    enable_parallel_processing: bool = Field(default=True, env="ENABLE_PARALLEL_PROCESSING")
    max_concurrent_jobs: int = Field(default=4, env="MAX_CONCURRENT_JOBS")


class DocuScanSettings(BaseSettings):
    """Main DocuScan application settings."""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Sub-configurations
    api: APISettings = Field(default_factory=APISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    elasticsearch: ElasticsearchSettings = Field(default_factory=ElasticsearchSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    ocr: OCRSettings = Field(default_factory=OCRSettings)
    nlp: NLPSettings = Field(default_factory=NLPSettings)
    file_upload: FileUploadSettings = Field(default_factory=FileUploadSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    ml: MLSettings = Field(default_factory=MLSettings)
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_nested_delimiter = "__"
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


# Global settings instance
settings = DocuScanSettings() 