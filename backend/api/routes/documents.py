"""
DocuScan Documents API Routes

This module provides comprehensive REST API endpoints for document management,
including upload, search, classification, statistics, and export functionality.
"""

import asyncio
import io
import json
import tempfile
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from pathlib import Path

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form,
    Query, BackgroundTasks, status
)
from fastapi.responses import StreamingResponse, JSONResponse
from loguru import logger
import pandas as pd

from backend.config import settings
from backend.models.document import (
    Document, DocumentResponse, DocumentDetailResponse,
    DocumentSearchRequest, DocumentSearchResponse, DocumentUpdateRequest,
    DocumentUploadRequest, CaseType, UrgencyLevel, DocumentStatus,
    DashboardStatistics, ExportRequest, ExportResponse, BatchProcessRequest,
    BatchProcessResponse
)
from backend.models.base import (
    SuccessResponse, ErrorResponse, PaginatedResponse,
    create_success_response, create_error_response
)
from backend.services.elasticsearch_service import ElasticsearchService
from backend.services.document_service import DocumentService
from backend.services.nlp_service import NLPService
from backend.services.ocr_service import OCRService


# Initialize router
router = APIRouter()


# Dependency to get services from the main app
async def get_elasticsearch_service():
    """Dependency to get Elasticsearch service."""
    # This will be injected by the main app
    pass


async def get_document_service():
    """Dependency to get Document service."""
    # This will be injected by the main app
    pass


@router.post("/upload", response_model=SuccessResponse[DocumentResponse])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    case_type_hint: Optional[CaseType] = Form(None),
    client_name_hint: Optional[str] = Form(None),
    urgency_hint: Optional[UrgencyLevel] = Form(None),
    tags: Optional[str] = Form(None),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Upload and process a legal document.
    
    Args:
        file: Document file to upload
        case_type_hint: Suggested case type
        client_name_hint: Suggested client name
        urgency_hint: Suggested urgency level
        tags: Comma-separated tags
        document_service: Document processing service
        
    Returns:
        SuccessResponse[DocumentResponse]: Upload result with document metadata
    """
    try:
        logger.info(f"📤 Uploading document: {file.filename}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Check file size
        max_size = settings.file_upload.max_file_size_mb * 1024 * 1024
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum of {settings.file_upload.max_file_size_mb}MB"
            )
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.file_upload.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_ext} not supported"
            )
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Create upload request
        upload_request = DocumentUploadRequest(
            filename=file.filename,
            content_type=file.content_type,
            case_type_hint=case_type_hint,
            client_name_hint=client_name_hint,
            urgency_hint=urgency_hint,
            tags=tag_list
        )
        
        # Process document
        document = await document_service.process_uploaded_file(file, upload_request)
        
        # Convert to response model
        response_doc = DocumentResponse(
            id=document.id,
            filename=document.filename,
            content_preview=document.content_preview or "",
            case_type=document.case_type,
            urgency_level=document.urgency_level,
            document_type=document.document_type,
            client_name=document.client_name,
            status=document.status,
            created_at=document.created_at,
            updated_at=document.updated_at,
            tags=document.tags,
            keywords=document.keywords
        )
        
        logger.info(f"✅ Document uploaded successfully: {document.id}")
        
        return create_success_response(
            data=response_doc,
            message=f"Document '{file.filename}' uploaded and processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )


@router.get("/search", response_model=SuccessResponse[DocumentSearchResponse])
async def search_documents(
    query: Optional[str] = Query(None, description="Search query"),
    case_types: Optional[List[CaseType]] = Query(None, description="Filter by case types"),
    urgency_levels: Optional[List[UrgencyLevel]] = Query(None, description="Filter by urgency"),
    client_names: Optional[List[str]] = Query(None, description="Filter by client names"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    status: Optional[List[DocumentStatus]] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset"),
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    elasticsearch_service: ElasticsearchService = Depends(get_elasticsearch_service)
):
    """
    Search documents with advanced filtering and sorting.
    
    Args:
        query: Text search query
        case_types: Filter by case types
        urgency_levels: Filter by urgency levels
        client_names: Filter by client names
        tags: Filter by tags
        date_from: Filter from date
        date_to: Filter to date
        status: Filter by processing status
        limit: Results limit (max 100)
        offset: Results offset
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        elasticsearch_service: Elasticsearch service
        
    Returns:
        SuccessResponse[DocumentSearchResponse]: Search results
    """
    try:
        logger.info(f"🔍 Searching documents: query='{query}', limit={limit}, offset={offset}")
        
        # Build search request
        search_request = DocumentSearchRequest(
            query=query,
            case_types=case_types or [],
            urgency_levels=urgency_levels or [],
            client_names=client_names or [],
            tags=tags or [],
            date_from=date_from,
            date_to=date_to,
            status=status or [],
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Execute search
        search_results = await elasticsearch_service.search_documents(search_request)
        
        logger.info(f"✅ Search completed: {search_results.total} total results")
        
        return create_success_response(
            data=search_results,
            message=f"Found {search_results.total} documents"
        )
        
    except Exception as e:
        logger.error(f"❌ Document search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document search failed: {str(e)}"
        )


@router.get("/{document_id}", response_model=SuccessResponse[DocumentDetailResponse])
async def get_document(
    document_id: UUID,
    elasticsearch_service: ElasticsearchService = Depends(get_elasticsearch_service)
):
    """
    Get detailed document information by ID.
    
    Args:
        document_id: Document identifier
        elasticsearch_service: Elasticsearch service
        
    Returns:
        SuccessResponse[DocumentDetailResponse]: Detailed document information
    """
    try:
        logger.info(f"📄 Retrieving document: {document_id}")
        
        # Get document from Elasticsearch
        document = await elasticsearch_service.get_document(str(document_id))
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        # Convert to detailed response
        response_doc = DocumentDetailResponse(
            id=document.id,
            filename=document.filename,
            content_preview=document.content_preview or "",
            case_type=document.case_type,
            urgency_level=document.urgency_level,
            document_type=document.document_type,
            client_name=document.client_name,
            status=document.status,
            created_at=document.created_at,
            updated_at=document.updated_at,
            tags=document.tags,
            keywords=document.keywords,
            content=document.content,
            entities=document.entities,
            summary=document.summary,
            metrics=document.metrics,
            date_created=document.date_created,
            deadline_date=document.deadline_date
        )
        
        logger.info(f"✅ Document retrieved: {document_id}")
        
        return create_success_response(
            data=response_doc,
            message="Document retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Document retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document retrieval failed: {str(e)}"
        )


@router.put("/{document_id}", response_model=SuccessResponse[DocumentResponse])
async def update_document(
    document_id: UUID,
    update_request: DocumentUpdateRequest,
    elasticsearch_service: ElasticsearchService = Depends(get_elasticsearch_service)
):
    """
    Update document metadata.
    
    Args:
        document_id: Document identifier
        update_request: Update data
        elasticsearch_service: Elasticsearch service
        
    Returns:
        SuccessResponse[DocumentResponse]: Updated document information
    """
    try:
        logger.info(f"📝 Updating document: {document_id}")
        
        # Prepare update data
        update_data = {}
        
        if update_request.case_type is not None:
            update_data["case_type"] = update_request.case_type
        if update_request.urgency_level is not None:
            update_data["urgency_level"] = update_request.urgency_level
        if update_request.client_name is not None:
            update_data["client_name"] = update_request.client_name
        if update_request.tags is not None:
            update_data["tags"] = update_request.tags
        if update_request.deadline_date is not None:
            update_data["deadline_date"] = update_request.deadline_date
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
        
        # Update document
        success = await elasticsearch_service.update_document(str(document_id), update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        # Get updated document
        updated_document = await elasticsearch_service.get_document(str(document_id))
        
        if not updated_document:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated document"
            )
        
        # Convert to response
        response_doc = DocumentResponse(
            id=updated_document.id,
            filename=updated_document.filename,
            content_preview=updated_document.content_preview or "",
            case_type=updated_document.case_type,
            urgency_level=updated_document.urgency_level,
            document_type=updated_document.document_type,
            client_name=updated_document.client_name,
            status=updated_document.status,
            created_at=updated_document.created_at,
            updated_at=updated_document.updated_at,
            tags=updated_document.tags,
            keywords=updated_document.keywords
        )
        
        logger.info(f"✅ Document updated: {document_id}")
        
        return create_success_response(
            data=response_doc,
            message="Document updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Document update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document update failed: {str(e)}"
        )


@router.delete("/{document_id}", response_model=SuccessResponse[Dict[str, str]])
async def delete_document(
    document_id: UUID,
    elasticsearch_service: ElasticsearchService = Depends(get_elasticsearch_service)
):
    """
    Delete a document.
    
    Args:
        document_id: Document identifier
        elasticsearch_service: Elasticsearch service
        
    Returns:
        SuccessResponse[Dict[str, str]]: Deletion confirmation
    """
    try:
        logger.info(f"🗑️ Deleting document: {document_id}")
        
        # Delete document
        success = await elasticsearch_service.delete_document(str(document_id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        logger.info(f"✅ Document deleted: {document_id}")
        
        return create_success_response(
            data={"document_id": str(document_id), "status": "deleted"},
            message="Document deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Document deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document deletion failed: {str(e)}"
        )


@router.get("/statistics/dashboard", response_model=SuccessResponse[DashboardStatistics])
async def get_dashboard_statistics(
    elasticsearch_service: ElasticsearchService = Depends(get_elasticsearch_service)
):
    """
    Get comprehensive dashboard statistics.
    
    Args:
        elasticsearch_service: Elasticsearch service
        
    Returns:
        SuccessResponse[DashboardStatistics]: Dashboard analytics data
    """
    try:
        logger.info("📊 Retrieving dashboard statistics")
        
        # Get statistics from Elasticsearch
        statistics = await elasticsearch_service.get_dashboard_statistics()
        
        logger.info(f"✅ Dashboard statistics retrieved: {statistics.total_documents} documents")
        
        return create_success_response(
            data=statistics,
            message="Dashboard statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Dashboard statistics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard statistics retrieval failed: {str(e)}"
        )


@router.post("/export", response_model=SuccessResponse[ExportResponse])
async def export_documents(
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    elasticsearch_service: ElasticsearchService = Depends(get_elasticsearch_service)
):
    """
    Export documents in specified format.
    
    Args:
        export_request: Export configuration
        background_tasks: Background task queue
        elasticsearch_service: Elasticsearch service
        
    Returns:
        SuccessResponse[ExportResponse]: Export job information
    """
    try:
        logger.info(f"📤 Starting document export: format={export_request.format}")
        
        # Generate export ID
        export_id = uuid4()
        
        # Add background task for export processing
        background_tasks.add_task(
            _process_export,
            export_id,
            export_request,
            elasticsearch_service
        )
        
        # Create export response
        export_response = ExportResponse(
            export_id=export_id,
            status="processing",
            created_at=datetime.utcnow()
        )
        
        logger.info(f"✅ Export job created: {export_id}")
        
        return create_success_response(
            data=export_response,
            message="Export job started successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Export job creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export job creation failed: {str(e)}"
        )


@router.get("/export/{export_id}/status", response_model=SuccessResponse[ExportResponse])
async def get_export_status(export_id: UUID):
    """
    Get export job status.
    
    Args:
        export_id: Export job identifier
        
    Returns:
        SuccessResponse[ExportResponse]: Export job status
    """
    try:
        logger.info(f"📊 Checking export status: {export_id}")
        
        # TODO: Implement export status tracking
        # For now, return a mock response
        export_response = ExportResponse(
            export_id=export_id,
            status="completed",
            download_url=f"/api/v1/documents/export/{export_id}/download",
            created_at=datetime.utcnow(),
            file_size=1024000,
            record_count=100
        )
        
        return create_success_response(
            data=export_response,
            message="Export status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Export status retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export status retrieval failed: {str(e)}"
        )


@router.get("/export/{export_id}/download")
async def download_export(export_id: UUID):
    """
    Download exported document file.
    
    Args:
        export_id: Export job identifier
        
    Returns:
        StreamingResponse: Exported file
    """
    try:
        logger.info(f"📥 Downloading export: {export_id}")
        
        # TODO: Implement actual export file retrieval
        # For now, return a sample CSV
        csv_data = "id,filename,case_type,urgency_level,client_name,created_at\n"
        csv_data += "123,sample.pdf,civil,medium,John Doe,2024-01-01T00:00:00Z\n"
        
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=export_{export_id}.csv"}
        )
        
    except Exception as e:
        logger.error(f"❌ Export download failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export download failed: {str(e)}"
        )


@router.post("/batch/process", response_model=SuccessResponse[BatchProcessResponse])
async def batch_process_documents(
    batch_request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Process multiple documents in batch.
    
    Args:
        batch_request: Batch processing request
        background_tasks: Background task queue
        document_service: Document processing service
        
    Returns:
        SuccessResponse[BatchProcessResponse]: Batch processing job information
    """
    try:
        logger.info(f"🔄 Starting batch processing: {len(batch_request.document_ids)} documents")
        
        # Generate batch ID
        batch_id = uuid4()
        
        # Add background task for batch processing
        background_tasks.add_task(
            _process_batch,
            batch_id,
            batch_request,
            document_service
        )
        
        # Create batch response
        batch_response = BatchProcessResponse(
            batch_id=batch_id,
            total_documents=len(batch_request.document_ids),
            status="processing",
            started_at=datetime.utcnow()
        )
        
        logger.info(f"✅ Batch processing job created: {batch_id}")
        
        return create_success_response(
            data=batch_response,
            message="Batch processing job started successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Batch processing job creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing job creation failed: {str(e)}"
        )


# Background task functions
async def _process_export(
    export_id: UUID,
    export_request: ExportRequest,
    elasticsearch_service: ElasticsearchService
):
    """Background task to process document export."""
    try:
        logger.info(f"🔄 Processing export: {export_id}")
        
        # Search for documents to export
        search_criteria = export_request.search_criteria or DocumentSearchRequest()
        search_results = await elasticsearch_service.search_documents(search_criteria)
        
        # Generate export file based on format
        if export_request.format == "csv":
            # Create CSV export
            df_data = []
            for doc in search_results.documents:
                row = {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "case_type": doc.case_type.value if doc.case_type else "",
                    "urgency_level": doc.urgency_level.value,
                    "client_name": doc.client_name or "",
                    "created_at": doc.created_at.isoformat(),
                    "tags": ",".join(doc.tags),
                    "keywords": ",".join(doc.keywords)
                }
                
                if export_request.include_content:
                    # Would need to fetch full document content
                    row["content"] = doc.content_preview
                
                df_data.append(row)
            
            # Save to file (in production, use proper file storage)
            df = pd.DataFrame(df_data)
            export_path = f"exports/{export_id}.csv"
            df.to_csv(export_path, index=False)
        
        logger.info(f"✅ Export completed: {export_id}")
        
    except Exception as e:
        logger.error(f"❌ Export processing failed: {e}")


async def _process_batch(
    batch_id: UUID,
    batch_request: BatchProcessRequest,
    document_service: DocumentService
):
    """Background task to process batch document operations."""
    try:
        logger.info(f"🔄 Processing batch: {batch_id}")
        
        # Process each document in the batch
        for doc_id in batch_request.document_ids:
            try:
                # Reprocess document if requested
                if batch_request.force_reprocess:
                    await document_service.reprocess_document(str(doc_id))
                    logger.info(f"✅ Reprocessed document: {doc_id}")
                
            except Exception as e:
                logger.error(f"❌ Failed to process document {doc_id}: {e}")
        
        logger.info(f"✅ Batch processing completed: {batch_id}")
        
    except Exception as e:
        logger.error(f"❌ Batch processing failed: {e}") 