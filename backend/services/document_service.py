import os
import uuid
import mimetypes
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import aiofiles
from loguru import logger

from config import settings
from models.document import (
    DocumentInDB, DocumentStatus, DocumentResponse, 
    DocumentSearchRequest, DocumentSearchResponse,
    CaseType, UrgencyLevel
)
from services.ocr_service import ocr_service
from services.nlp_service import nlp_service
from services.elasticsearch_service import elasticsearch_service


class DocumentService:
    """Service for managing document lifecycle"""
    
    def __init__(self):
        """Initialize document service"""
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def process_uploaded_file(
        self, 
        filename: str, 
        file_content: bytes, 
        original_filename: str
    ) -> Optional[DocumentResponse]:
        """
        Process an uploaded file through the complete pipeline
        
        Args:
            filename: Generated filename for storage
            file_content: File content bytes
            original_filename: Original filename from upload
            
        Returns:
            Processed document or None if failed
        """
        try:
            # Generate unique document ID
            document_id = str(uuid.uuid4())
            
            # Create file path
            file_path = self.upload_dir / filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Get file info
            file_size = len(file_content)
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            if not mime_type:
                mime_type = "application/octet-stream"
            
            # Create initial document record
            document_data = {
                "id": document_id,
                "filename": filename,
                "original_filename": original_filename,
                "file_path": str(file_path),
                "text_content": None,
                "summary": None,
                "case_type": None,
                "client_name": None,
                "urgency_level": UrgencyLevel.MEDIUM,
                "tags": [],
                "extracted_entities": {},
                "confidence_scores": {},
                "status": DocumentStatus.UPLOADED,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "file_size": file_size,
                "mime_type": mime_type
            }
            
            # Index initial document
            await elasticsearch_service.index_document(document_data)
            
            # Start background processing
            await self._process_document_content(document_id, str(file_path), mime_type)
            
            return DocumentResponse(**document_data)
            
        except Exception as e:
            logger.error(f"Error processing uploaded file {original_filename}: {str(e)}")
            return None
    
    async def _process_document_content(
        self, 
        document_id: str, 
        file_path: str, 
        mime_type: str
    ):
        """
        Process document content (OCR + NLP)
        
        Args:
            document_id: Document ID
            file_path: Path to the file
            mime_type: MIME type of the file
        """
        try:
            # Update status to processing
            await elasticsearch_service.update_document(
                document_id, 
                {"status": DocumentStatus.PROCESSING}
            )
            
            # Extract text using OCR
            logger.info(f"Starting OCR for document {document_id}")
            text_content = await ocr_service.extract_text(file_path, mime_type)
            
            if not text_content:
                logger.warning(f"No text extracted from document {document_id}")
                await elasticsearch_service.update_document(
                    document_id,
                    {"status": DocumentStatus.FAILED}
                )
                return
            
            # Classify document using NLP
            logger.info(f"Starting NLP classification for document {document_id}")
            classification_result = await nlp_service.classify_document(text_content)
            
            # Prepare update data
            update_data = {
                "text_content": text_content,
                "summary": classification_result.get("summary", ""),
                "case_type": classification_result.get("case_type"),
                "urgency_level": classification_result.get("urgency_level"),
                "tags": classification_result.get("tags", []),
                "extracted_entities": classification_result.get("entities", {}),
                "confidence_scores": classification_result.get("confidence_scores", {}),
                "status": DocumentStatus.PROCESSED
            }
            
            # Extract client name from classification
            client_names = classification_result.get("client_names", [])
            if client_names:
                update_data["client_name"] = client_names[0]  # Use first client name
            
            # Update document in Elasticsearch
            success = await elasticsearch_service.update_document(document_id, update_data)
            
            if success:
                logger.info(f"Successfully processed document {document_id}")
            else:
                logger.error(f"Failed to update document {document_id} in Elasticsearch")
                
        except Exception as e:
            logger.error(f"Error processing document content for {document_id}: {str(e)}")
            # Update status to failed
            await elasticsearch_service.update_document(
                document_id,
                {"status": DocumentStatus.FAILED}
            )
    
    async def get_document_by_id(self, document_id: str) -> Optional[DocumentResponse]:
        """Get document by ID"""
        try:
            doc_data = await elasticsearch_service.get_document_by_id(document_id)
            if doc_data:
                return DocumentResponse(**doc_data)
            return None
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {str(e)}")
            return None
    
    async def search_documents(self, search_request: DocumentSearchRequest) -> DocumentSearchResponse:
        """Search documents"""
        try:
            results = await elasticsearch_service.search_documents(search_request)
            
            documents = []
            for doc_data in results["documents"]:
                try:
                    documents.append(DocumentResponse(**doc_data))
                except Exception as e:
                    logger.warning(f"Error converting document data: {str(e)}")
                    continue
            
            return DocumentSearchResponse(
                documents=documents,
                total=results["total"],
                limit=results["limit"],
                offset=results["offset"]
            )
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return DocumentSearchResponse(
                documents=[],
                total=0,
                limit=search_request.limit,
                offset=search_request.offset
            )
    
    async def update_document(
        self, 
        document_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[DocumentResponse]:
        """Update document metadata"""
        try:
            # Update in Elasticsearch
            success = await elasticsearch_service.update_document(document_id, update_data)
            
            if success:
                return await self.get_document_by_id(document_id)
            return None
            
        except Exception as e:
            logger.error(f"Error updating document {document_id}: {str(e)}")
            return None
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document and its file"""
        try:
            # Get document info first
            doc_data = await elasticsearch_service.get_document_by_id(document_id)
            
            if doc_data:
                # Delete file from filesystem
                file_path = Path(doc_data.get("file_path", ""))
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted file: {file_path}")
            
            # Delete from Elasticsearch
            success = await elasticsearch_service.delete_document(document_id)
            
            if success:
                logger.info(f"Successfully deleted document {document_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    async def get_document_statistics(self) -> Dict[str, Any]:
        """Get document statistics for dashboard"""
        try:
            aggs = await elasticsearch_service.get_aggregations()
            
            # Process aggregations
            stats = {
                "total_documents": 0,
                "case_types": {},
                "urgency_levels": {},
                "top_clients": {},
                "documents_by_date": {}
            }
            
            # Case types
            if "case_types" in aggs:
                for bucket in aggs["case_types"]["buckets"]:
                    stats["case_types"][bucket["key"]] = bucket["doc_count"]
                    stats["total_documents"] += bucket["doc_count"]
            
            # Urgency levels
            if "urgency_levels" in aggs:
                for bucket in aggs["urgency_levels"]["buckets"]:
                    stats["urgency_levels"][bucket["key"]] = bucket["doc_count"]
            
            # Top clients
            if "top_clients" in aggs:
                for bucket in aggs["top_clients"]["buckets"]:
                    stats["top_clients"][bucket["key"]] = bucket["doc_count"]
            
            # Documents by date
            if "documents_by_date" in aggs:
                for bucket in aggs["documents_by_date"]["buckets"]:
                    stats["documents_by_date"][bucket["key_as_string"]] = bucket["doc_count"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting document statistics: {str(e)}")
            return {
                "total_documents": 0,
                "case_types": {},
                "urgency_levels": {},
                "top_clients": {},
                "documents_by_date": {}
            }
    
    async def export_documents(
        self, 
        search_request: DocumentSearchRequest,
        format: str = "json"
    ) -> Optional[bytes]:
        """Export documents in specified format"""
        try:
            # Get all matching documents
            search_request.limit = 1000  # Limit export size
            results = await self.search_documents(search_request)
            
            if format.lower() == "json":
                import json
                data = {
                    "documents": [doc.dict() for doc in results.documents],
                    "total": results.total,
                    "exported_at": datetime.utcnow().isoformat()
                }
                return json.dumps(data, indent=2, default=str).encode('utf-8')
            
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                if results.documents:
                    fieldnames = [
                        "id", "filename", "case_type", "client_name", 
                        "urgency_level", "summary", "created_at", "file_size"
                    ]
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for doc in results.documents:
                        row = {
                            "id": doc.id,
                            "filename": doc.original_filename,
                            "case_type": doc.case_type,
                            "client_name": doc.client_name or "",
                            "urgency_level": doc.urgency_level,
                            "summary": doc.summary or "",
                            "created_at": doc.created_at,
                            "file_size": doc.file_size
                        }
                        writer.writerow(row)
                
                return output.getvalue().encode('utf-8')
            
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
                
        except Exception as e:
            logger.error(f"Error exporting documents: {str(e)}")
            return None
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types"""
        return list(settings.allowed_extensions)


# Global document service instance
document_service = DocumentService()