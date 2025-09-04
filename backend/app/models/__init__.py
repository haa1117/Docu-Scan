"""
DocuScan Models Package

This package contains all data models for the DocuScan application.
"""

from .document import *
from .user import *
from .auth import *

__all__ = [
    # Document models
    "Document",
    "DocumentType",
    "CaseType", 
    "UrgencyLevel",
    "DocumentStatus",
    "EntityType",
    "OCRResult",
    "NamedEntity",
    "DocumentSummary",
    "ClassificationResult",
    "ProcessingMetrics",
    "DocumentUploadRequest",
    "DocumentUpdateRequest",
    "DocumentSearchRequest",
    "DocumentResponse",
    "DocumentSearchResponse",
    "DashboardStatistics",
    "ExportRequest",
    "ExportResponse",
    "BatchProcessingRequest",
    "BatchProcessingResponse",
    
    # User models
    "User",
    "UserRole",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    
    # Auth models
    "Token",
    "TokenData",
    "LoginRequest",
    "LoginResponse",
] 