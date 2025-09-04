"""
DocuScan Production Document Models

Comprehensive data models for the legal document classification system
with OCR, NLP, authentication, and advanced features.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator, root_validator
import json


class DocumentType(str, Enum):
    """Document file types."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    TIFF = "tiff"
    BMP = "bmp"
    GIF = "gif"
    XLSX = "xlsx"
    PPTX = "pptx"


class CaseType(str, Enum):
    """Legal case types."""
    CRIMINAL = "criminal"
    CIVIL = "civil"
    CORPORATE = "corporate"
    FAMILY = "family"
    IMMIGRATION = "immigration"
    EMPLOYMENT = "employment"
    REAL_ESTATE = "real_estate"
    TAX = "tax"
    BANKRUPTCY = "bankruptcy"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    CONTRACT = "contract"
    LITIGATION = "litigation"
    REGULATORY = "regulatory"
    COMPLIANCE = "compliance"
    MERGERS_ACQUISITIONS = "mergers_acquisitions"


class UrgencyLevel(str, Enum):
    """Document urgency levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    OCR_COMPLETE = "ocr_complete"
    NLP_COMPLETE = "nlp_complete"
    COMPLETE = "complete"
    FAILED = "failed"
    ARCHIVED = "archived"


class EntityType(str, Enum):
    """Named entity types."""
    PERSON = "PERSON"
    ORGANIZATION = "ORG"
    MONEY = "MONEY"
    DATE = "DATE"
    LOCATION = "GPE"
    LAW = "LAW"
    EVENT = "EVENT"
    PRODUCT = "PRODUCT"
    LEGAL_ENTITY = "LEGAL_ENTITY"
    CASE_NUMBER = "CASE_NUMBER"
    CONTRACT_TERM = "CONTRACT_TERM"


class ProcessingStage(str, Enum):
    """Document processing stages."""
    UPLOAD = "upload"
    VALIDATION = "validation"
    OCR = "ocr"
    NLP = "nlp"
    CLASSIFICATION = "classification"
    INDEXING = "indexing"
    COMPLETION = "completion"


# Base Models
class BaseTimestampModel(BaseModel):
    """Base model with timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OCRResult(BaseModel):
    """OCR processing results."""
    text: str = Field(..., description="Extracted text content")
    confidence: float = Field(..., ge=0, le=1, description="Overall OCR confidence")
    page_count: int = Field(..., ge=1, description="Number of pages processed")
    language_detected: str = Field(..., description="Detected language")
    processing_time_seconds: float = Field(..., description="OCR processing time")
    
    # Detailed results per page
    page_results: List[Dict[str, Any]] = Field(default_factory=list, description="Per-page OCR results")
    
    # OCR metadata
    tesseract_version: str = Field(..., description="Tesseract version used")
    psm_mode: int = Field(..., description="Page segmentation mode")
    oem_mode: int = Field(..., description="OCR engine mode")
    dpi: int = Field(..., description="Image DPI used")


class NamedEntity(BaseModel):
    """Named entity extracted from document."""
    text: str = Field(..., description="Entity text")
    label: EntityType = Field(..., description="Entity type")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    
    # Additional metadata
    canonical_form: Optional[str] = Field(None, description="Normalized entity form")
    context: Optional[str] = Field(None, description="Surrounding context")
    source_page: Optional[int] = Field(None, description="Source page number")


class DocumentSummary(BaseModel):
    """Document summary and key insights."""
    summary_text: str = Field(..., description="Generated summary")
    key_points: List[str] = Field(default_factory=list, description="Key points extracted")
    topics: List[str] = Field(default_factory=list, description="Main topics")
    keywords: List[str] = Field(default_factory=list, description="Important keywords")
    
    # Summary metadata
    original_length: int = Field(..., description="Original text length")
    summary_length: int = Field(..., description="Summary text length")
    compression_ratio: float = Field(..., description="Compression ratio")
    confidence: float = Field(..., ge=0, le=1, description="Summary quality confidence")
    
    # Legal-specific insights
    parties_mentioned: List[str] = Field(default_factory=list, description="Legal parties")
    dates_mentioned: List[str] = Field(default_factory=list, description="Important dates")
    amounts_mentioned: List[str] = Field(default_factory=list, description="Financial amounts")


class ClassificationResult(BaseModel):
    """Document classification results."""
    case_type: CaseType = Field(..., description="Predicted case type")
    case_type_confidence: float = Field(..., ge=0, le=1, description="Case type confidence")
    
    urgency_level: UrgencyLevel = Field(..., description="Predicted urgency level")
    urgency_confidence: float = Field(..., ge=0, le=1, description="Urgency confidence")
    
    # Alternative classifications
    alternative_case_types: List[Dict[str, float]] = Field(default_factory=list, description="Alternative case types with confidence")
    
    # Classification reasoning
    classification_reasons: List[str] = Field(default_factory=list, description="Reasons for classification")
    urgency_indicators: List[str] = Field(default_factory=list, description="Urgency indicators found")


class ProcessingMetrics(BaseModel):
    """Document processing performance metrics."""
    upload_time_seconds: float = Field(..., description="File upload time")
    ocr_time_seconds: float = Field(..., description="OCR processing time")
    nlp_time_seconds: float = Field(..., description="NLP processing time")
    classification_time_seconds: float = Field(..., description="Classification time")
    indexing_time_seconds: float = Field(..., description="Elasticsearch indexing time")
    total_time_seconds: float = Field(..., description="Total processing time")
    
    # File metrics
    file_size_bytes: int = Field(..., description="Original file size")
    text_length_chars: int = Field(..., description="Extracted text length")
    
    # Quality metrics
    ocr_quality_score: float = Field(..., ge=0, le=1, description="OCR quality assessment")
    text_quality_score: float = Field(..., ge=0, le=1, description="Text quality assessment")
    
    # Resource usage
    memory_used_mb: float = Field(..., description="Peak memory usage")
    cpu_time_seconds: float = Field(..., description="CPU time used")


class DocumentAuditLog(BaseModel):
    """Document audit trail entry."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stage: ProcessingStage = Field(..., description="Processing stage")
    status: str = Field(..., description="Stage status")
    message: str = Field(..., description="Log message")
    user_id: Optional[UUID] = Field(None, description="User who triggered the action")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Document(BaseTimestampModel):
    """Main document model with all processing results."""
    
    # Core document information
    id: UUID = Field(default_factory=uuid4, description="Unique document ID")
    filename: str = Field(..., description="Original filename")
    original_filename: str = Field(..., description="Original filename without modifications")
    file_path: str = Field(..., description="Storage path")
    file_size_bytes: int = Field(..., description="File size in bytes")
    file_hash: str = Field(..., description="File content hash")
    mime_type: str = Field(..., description="MIME type")
    document_type: DocumentType = Field(..., description="Document type")
    
    # Processing status
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED, description="Processing status")
    processing_progress: float = Field(default=0.0, ge=0, le=100, description="Processing progress percentage")
    
    # User and ownership
    uploaded_by: UUID = Field(..., description="User who uploaded the document")
    client_name: str = Field(..., description="Client name")
    client_names: List[str] = Field(default_factory=list, description="All client names mentioned")
    case_number: Optional[str] = Field(None, description="Case number")
    
    # Content and OCR results
    raw_content: Optional[str] = Field(None, description="Raw extracted content")
    cleaned_content: Optional[str] = Field(None, description="Cleaned and processed content")
    content_preview: Optional[str] = Field(None, description="Content preview for display")
    ocr_result: Optional[OCRResult] = Field(None, description="OCR processing results")
    
    # NLP and classification
    entities: List[NamedEntity] = Field(default_factory=list, description="Extracted named entities")
    summary: Optional[DocumentSummary] = Field(None, description="Document summary")
    classification: Optional[ClassificationResult] = Field(None, description="Classification results")
    
    # Legal metadata
    case_type: Optional[CaseType] = Field(None, description="Classified case type")
    urgency_level: Optional[UrgencyLevel] = Field(None, description="Urgency level")
    practice_areas: List[str] = Field(default_factory=list, description="Practice areas")
    legal_topics: List[str] = Field(default_factory=list, description="Legal topics")
    
    # Dates and deadlines
    document_date: Optional[date] = Field(None, description="Document creation date")
    deadline_date: Optional[date] = Field(None, description="Important deadline")
    effective_date: Optional[date] = Field(None, description="Effective date")
    expiration_date: Optional[date] = Field(None, description="Expiration date")
    
    # Tags and categorization
    tags: List[str] = Field(default_factory=list, description="User-defined tags")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata fields")
    
    # Processing metrics and audit
    metrics: Optional[ProcessingMetrics] = Field(None, description="Processing performance metrics")
    audit_log: List[DocumentAuditLog] = Field(default_factory=list, description="Processing audit trail")
    
    # Security and access
    is_confidential: bool = Field(default=False, description="Confidential document flag")
    access_level: str = Field(default="standard", description="Access level requirement")
    retention_date: Optional[date] = Field(None, description="Document retention until date")
    
    # Search and indexing
    search_vector: Optional[str] = Field(None, description="Search vector for full-text search")
    language: str = Field(default="en", description="Document language")
    
    @validator('content_preview', always=True)
    def generate_content_preview(cls, v, values):
        """Generate content preview from raw content."""
        if v:
            return v
        raw_content = values.get('raw_content', '')
        if raw_content:
            return raw_content[:500] + "..." if len(raw_content) > 500 else raw_content
        return ""
    
    @root_validator
    def validate_dates(cls, values):
        """Validate date relationships."""
        document_date = values.get('document_date')
        deadline_date = values.get('deadline_date')
        effective_date = values.get('effective_date')
        expiration_date = values.get('expiration_date')
        
        if effective_date and expiration_date and effective_date > expiration_date:
            raise ValueError("Effective date cannot be after expiration date")
        
        return values


# Request/Response Models
class DocumentUploadRequest(BaseModel):
    """Document upload request."""
    client_name: str = Field(..., description="Client name")
    case_number: Optional[str] = Field(None, description="Case number")
    tags: List[str] = Field(default_factory=list, description="Initial tags")
    is_confidential: bool = Field(default=False, description="Confidential flag")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class DocumentUpdateRequest(BaseModel):
    """Document update request."""
    client_name: Optional[str] = Field(None, description="Client name")
    case_number: Optional[str] = Field(None, description="Case number")
    tags: Optional[List[str]] = Field(None, description="Tags")
    case_type: Optional[CaseType] = Field(None, description="Manual case type override")
    urgency_level: Optional[UrgencyLevel] = Field(None, description="Manual urgency override")
    is_confidential: Optional[bool] = Field(None, description="Confidential flag")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom metadata")


class DocumentSearchRequest(BaseModel):
    """Document search request."""
    query: Optional[str] = Field(None, description="Search query")
    case_types: Optional[List[CaseType]] = Field(None, description="Filter by case types")
    urgency_levels: Optional[List[UrgencyLevel]] = Field(None, description="Filter by urgency levels")
    client_names: Optional[List[str]] = Field(None, description="Filter by client names")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    date_from: Optional[date] = Field(None, description="Filter from date")
    date_to: Optional[date] = Field(None, description="Filter to date")
    is_confidential: Optional[bool] = Field(None, description="Filter by confidential flag")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")


class DocumentResponse(BaseModel):
    """Document response model."""
    id: UUID
    filename: str
    client_name: str
    case_type: Optional[CaseType]
    urgency_level: Optional[UrgencyLevel]
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    content_preview: Optional[str]
    tags: List[str]
    file_size_bytes: int
    processing_progress: float
    
    # Summary information
    summary_text: Optional[str] = None
    entity_count: int = 0
    keyword_count: int = 0
    
    @validator('summary_text', always=True)
    def extract_summary_text(cls, v, values):
        """Extract summary text for response."""
        # This would be populated from the full document's summary
        return v
    
    @validator('entity_count', always=True)
    def count_entities(cls, v, values):
        """Count entities for response."""
        # This would be populated from the full document's entities
        return v
    
    @validator('keyword_count', always=True)
    def count_keywords(cls, v, values):
        """Count keywords for response."""
        # This would be populated from the full document's keywords
        return v


class DocumentSearchResponse(BaseModel):
    """Document search response."""
    documents: List[DocumentResponse]
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")
    
    @validator('total_pages', always=True)
    def calculate_total_pages(cls, v, values):
        """Calculate total pages."""
        total = values.get('total', 0)
        size = values.get('size', 20)
        return (total + size - 1) // size if total > 0 else 0
    
    @validator('has_next', always=True)
    def calculate_has_next(cls, v, values):
        """Calculate if has next page."""
        page = values.get('page', 1)
        total_pages = values.get('total_pages', 0)
        return page < total_pages
    
    @validator('has_previous', always=True)
    def calculate_has_previous(cls, v, values):
        """Calculate if has previous page."""
        page = values.get('page', 1)
        return page > 1


# Dashboard and Analytics Models
class CaseTypeStatistics(BaseModel):
    """Case type statistics."""
    case_type: CaseType
    count: int
    percentage: float
    avg_processing_time: float
    urgent_count: int


class UrgencyStatistics(BaseModel):
    """Urgency level statistics."""
    urgency_level: UrgencyLevel
    count: int
    percentage: float
    avg_resolution_time: Optional[float] = None


class ClientStatistics(BaseModel):
    """Client statistics."""
    client_name: str
    document_count: int
    recent_activity: datetime
    case_types: List[str]
    urgent_documents: int


class TimelineDataPoint(BaseModel):
    """Timeline data point for charts."""
    date: date
    count: int
    case_type_breakdown: Dict[str, int] = Field(default_factory=dict)


class DashboardStatistics(BaseModel):
    """Comprehensive dashboard statistics."""
    total_documents: int
    high_priority_count: int
    critical_priority_count: int
    active_clients: int
    documents_today: int
    documents_this_week: int
    documents_this_month: int
    
    # Processing statistics
    avg_processing_time_minutes: float
    processing_queue_size: int
    failed_documents_count: int
    
    # Distribution data
    case_type_distribution: List[CaseTypeStatistics]
    urgency_distribution: List[UrgencyStatistics]
    top_clients: List[ClientStatistics]
    upload_timeline: List[TimelineDataPoint]
    
    # System health
    system_status: str = "healthy"
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# Export Models
class ExportRequest(BaseModel):
    """Data export request."""
    search_criteria: DocumentSearchRequest
    export_format: str = Field("csv", description="Export format (csv, excel, json)")
    include_content: bool = Field(False, description="Include full document content")
    include_metadata: bool = Field(True, description="Include metadata")
    
    # Field selection
    fields: Optional[List[str]] = Field(None, description="Specific fields to export")


class ExportResponse(BaseModel):
    """Export response."""
    export_id: UUID = Field(default_factory=uuid4)
    status: str
    download_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    
    @validator('expires_at', always=True)
    def set_expiration(cls, v, values):
        """Set export expiration."""
        if not v:
            created = values.get('created_at', datetime.utcnow())
            return created.replace(hour=created.hour + 24)  # 24-hour expiration
        return v


# Batch Processing Models
class BatchProcessingRequest(BaseModel):
    """Batch processing request."""
    document_ids: List[UUID]
    operation: str = Field(..., description="Batch operation (reprocess, reclassify, archive, delete)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")


class BatchProcessingResponse(BaseModel):
    """Batch processing response."""
    batch_id: UUID = Field(default_factory=uuid4)
    total_documents: int
    status: str = "initiated"
    progress: float = 0.0
    completed_count: int = 0
    failed_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_completion: Optional[datetime] = None 