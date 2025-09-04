"""
DocuScan Document Models

This module provides comprehensive Pydantic models for document handling,
classification, and API interactions with type safety and validation.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator
from uuid import UUID, uuid4


class CaseType(str, Enum):
    """Legal case type enumeration."""
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


class UrgencyLevel(str, Enum):
    """Document urgency level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentStatus(str, Enum):
    """Document processing status enumeration."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    OCR_COMPLETE = "ocr_complete"
    NLP_COMPLETE = "nlp_complete"
    CLASSIFIED = "classified"
    INDEXED = "indexed"
    COMPLETE = "complete"
    ERROR = "error"


class DocumentType(str, Enum):
    """Document type enumeration."""
    PDF = "pdf"
    WORD = "word"
    TEXT = "text"
    IMAGE = "image"
    SCANNED = "scanned"


class EntityType(str, Enum):
    """Named entity type enumeration."""
    PERSON = "PERSON"
    ORGANIZATION = "ORG"
    DATE = "DATE"
    MONEY = "MONEY"
    LOCATION = "GPE"
    MISC = "MISC"


# Base Models
class BaseDocumentModel(BaseModel):
    """Base model for all document-related models."""
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


# Entity Models
class NamedEntity(BaseDocumentModel):
    """Named entity extracted from document."""
    text: str = Field(..., description="Entity text")
    label: EntityType = Field(..., description="Entity type")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class DocumentSummary(BaseDocumentModel):
    """Document summary information."""
    sentences: List[str] = Field(..., description="Key sentences")
    keywords: List[str] = Field(..., description="Important keywords")
    topics: List[str] = Field(..., description="Main topics")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Summary confidence")


class ProcessingMetrics(BaseDocumentModel):
    """Document processing performance metrics."""
    ocr_time_seconds: Optional[float] = Field(None, description="OCR processing time")
    nlp_time_seconds: Optional[float] = Field(None, description="NLP processing time")
    total_time_seconds: Optional[float] = Field(None, description="Total processing time")
    file_size_bytes: Optional[int] = Field(None, description="Original file size")
    text_length: Optional[int] = Field(None, description="Extracted text length")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Processing confidence scores")


# Main Document Model
class Document(BaseDocumentModel):
    """Complete document model with all metadata."""
    
    # Identifiers
    id: UUID = Field(default_factory=uuid4, description="Unique document ID")
    filename: str = Field(..., description="Original filename")
    
    # Content
    content: str = Field(..., description="Full document text content")
    content_preview: Optional[str] = Field(None, description="Content preview (first 500 chars)")
    
    # Classification
    case_type: Optional[CaseType] = Field(None, description="Classified case type")
    urgency_level: UrgencyLevel = Field(default=UrgencyLevel.MEDIUM, description="Document urgency")
    document_type: DocumentType = Field(..., description="Document format type")
    
    # Metadata
    client_name: Optional[str] = Field(None, description="Extracted client name")
    client_names: List[str] = Field(default_factory=list, description="All potential client names")
    date_created: Optional[date] = Field(None, description="Document creation date")
    deadline_date: Optional[date] = Field(None, description="Document deadline")
    
    # Processing
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED, description="Processing status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    
    # Analysis Results
    entities: List[NamedEntity] = Field(default_factory=list, description="Extracted named entities")
    summary: Optional[DocumentSummary] = Field(None, description="Document summary")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    keywords: List[str] = Field(default_factory=list, description="Important keywords")
    
    # Technical Details
    file_path: Optional[str] = Field(None, description="File storage path")
    mime_type: Optional[str] = Field(None, description="File MIME type")
    file_hash: Optional[str] = Field(None, description="File content hash")
    language: str = Field(default="en", description="Document language")
    
    # Performance Metrics
    metrics: ProcessingMetrics = Field(default_factory=ProcessingMetrics, description="Processing metrics")
    
    @validator('content_preview', always=True)
    def generate_content_preview(cls, v, values):
        """Generate content preview from full content."""
        if v is None and 'content' in values:
            content = values['content']
            return content[:500] + "..." if len(content) > 500 else content
        return v
    
    @validator('updated_at', always=True)
    def update_timestamp(cls, v):
        """Always update the timestamp."""
        return datetime.utcnow()
    
    @root_validator
    def validate_dates(cls, values):
        """Validate date relationships."""
        created_at = values.get('created_at')
        deadline_date = values.get('deadline_date')
        
        if created_at and deadline_date:
            if deadline_date < created_at.date():
                # If deadline is in the past, mark as high urgency
                values['urgency_level'] = UrgencyLevel.HIGH
        
        return values


# Request/Response Models
class DocumentUploadRequest(BaseDocumentModel):
    """Document upload request model."""
    filename: str = Field(..., description="Original filename")
    content_type: Optional[str] = Field(None, description="File content type")
    case_type_hint: Optional[CaseType] = Field(None, description="Suggested case type")
    client_name_hint: Optional[str] = Field(None, description="Suggested client name")
    urgency_hint: Optional[UrgencyLevel] = Field(None, description="Suggested urgency level")
    tags: List[str] = Field(default_factory=list, description="Initial tags")


class DocumentResponse(BaseDocumentModel):
    """Document response model for API."""
    id: UUID
    filename: str
    content_preview: str
    case_type: Optional[CaseType]
    urgency_level: UrgencyLevel
    document_type: DocumentType
    client_name: Optional[str]
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    keywords: List[str]
    
    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    """Detailed document response with full content."""
    content: str
    entities: List[NamedEntity]
    summary: Optional[DocumentSummary]
    metrics: ProcessingMetrics
    date_created: Optional[date]
    deadline_date: Optional[date]


class DocumentSearchRequest(BaseDocumentModel):
    """Document search request model."""
    query: Optional[str] = Field(None, description="Search query")
    case_types: List[CaseType] = Field(default_factory=list, description="Filter by case types")
    urgency_levels: List[UrgencyLevel] = Field(default_factory=list, description="Filter by urgency")
    client_names: List[str] = Field(default_factory=list, description="Filter by client names")
    tags: List[str] = Field(default_factory=list, description="Filter by tags")
    date_from: Optional[date] = Field(None, description="Filter from date")
    date_to: Optional[date] = Field(None, description="Filter to date")
    status: List[DocumentStatus] = Field(default_factory=list, description="Filter by status")
    limit: int = Field(default=20, ge=1, le=100, description="Results limit")
    offset: int = Field(default=0, ge=0, description="Results offset")
    sort_by: str = Field(default="updated_at", description="Sort field")
    sort_order: str = Field(default="desc", regex="^(asc|desc)$", description="Sort order")


class DocumentSearchResponse(BaseDocumentModel):
    """Document search response model."""
    documents: List[DocumentResponse]
    total: int = Field(..., description="Total matching documents")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")
    has_more: bool = Field(..., description="More results available")
    
    @validator('has_more', always=True)
    def calculate_has_more(cls, v, values):
        """Calculate if more results are available."""
        total = values.get('total', 0)
        limit = values.get('limit', 20)
        offset = values.get('offset', 0)
        return (offset + limit) < total


class DocumentUpdateRequest(BaseDocumentModel):
    """Document update request model."""
    case_type: Optional[CaseType] = Field(None, description="Update case type")
    urgency_level: Optional[UrgencyLevel] = Field(None, description="Update urgency level")
    client_name: Optional[str] = Field(None, description="Update client name")
    tags: Optional[List[str]] = Field(None, description="Update tags")
    deadline_date: Optional[date] = Field(None, description="Update deadline")


# Statistics Models
class CaseTypeStatistics(BaseDocumentModel):
    """Case type distribution statistics."""
    case_type: CaseType
    count: int
    percentage: float = Field(..., ge=0.0, le=100.0)


class UrgencyStatistics(BaseDocumentModel):
    """Urgency level distribution statistics."""
    urgency_level: UrgencyLevel
    count: int
    percentage: float = Field(..., ge=0.0, le=100.0)


class ClientStatistics(BaseDocumentModel):
    """Client statistics."""
    client_name: str
    document_count: int
    case_types: List[CaseType]
    latest_document: datetime


class TimelineDataPoint(BaseDocumentModel):
    """Timeline data point for document uploads."""
    date: date
    count: int
    case_types: Dict[CaseType, int] = Field(default_factory=dict)


class DashboardStatistics(BaseDocumentModel):
    """Dashboard statistics summary."""
    total_documents: int = Field(..., description="Total document count")
    high_priority_count: int = Field(..., description="High priority documents")
    critical_priority_count: int = Field(..., description="Critical priority documents")
    active_clients: int = Field(..., description="Number of active clients")
    
    case_type_distribution: List[CaseTypeStatistics] = Field(..., description="Case type breakdown")
    urgency_distribution: List[UrgencyStatistics] = Field(..., description="Urgency breakdown")
    top_clients: List[ClientStatistics] = Field(..., description="Top clients by document count")
    upload_timeline: List[TimelineDataPoint] = Field(..., description="Document upload timeline")
    
    processing_stats: Dict[str, Any] = Field(default_factory=dict, description="Processing statistics")
    system_health: Dict[str, Any] = Field(default_factory=dict, description="System health metrics")


# Export Models
class ExportRequest(BaseDocumentModel):
    """Document export request model."""
    format: str = Field(..., regex="^(json|csv|xlsx)$", description="Export format")
    search_criteria: Optional[DocumentSearchRequest] = Field(None, description="Search criteria for export")
    include_content: bool = Field(default=False, description="Include full document content")
    include_entities: bool = Field(default=True, description="Include extracted entities")
    include_summary: bool = Field(default=True, description="Include document summary")


class ExportResponse(BaseDocumentModel):
    """Document export response model."""
    export_id: UUID = Field(default_factory=uuid4, description="Export job ID")
    status: str = Field(..., description="Export status")
    download_url: Optional[str] = Field(None, description="Download URL when ready")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Export creation time")
    expires_at: Optional[datetime] = Field(None, description="Download expiration time")
    file_size: Optional[int] = Field(None, description="Export file size in bytes")
    record_count: Optional[int] = Field(None, description="Number of exported records")


# Batch Processing Models
class BatchProcessRequest(BaseDocumentModel):
    """Batch document processing request."""
    document_ids: List[UUID] = Field(..., description="Document IDs to process")
    force_reprocess: bool = Field(default=False, description="Force reprocessing")
    processing_options: Dict[str, Any] = Field(default_factory=dict, description="Processing options")


class BatchProcessResponse(BaseDocumentModel):
    """Batch processing response."""
    batch_id: UUID = Field(default_factory=uuid4, description="Batch processing ID")
    total_documents: int = Field(..., description="Total documents in batch")
    status: str = Field(..., description="Batch processing status")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Processing progress percentage")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Batch start time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    failed_documents: List[UUID] = Field(default_factory=list, description="Failed document IDs")
    completed_documents: List[UUID] = Field(default_factory=list, description="Completed document IDs") 