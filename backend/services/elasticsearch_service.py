"""
DocuScan Elasticsearch Service

This module provides comprehensive Elasticsearch integration for document
indexing, searching, and analytics with proper error handling and monitoring.
"""

import asyncio
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import (
    ConnectionError, NotFoundError, RequestError, 
    AuthenticationException, TransportError
)
from loguru import logger

from config import settings
from models.document import (
    Document, DocumentSearchRequest, DocumentSearchResponse,
    DocumentResponse, CaseType, UrgencyLevel, DocumentStatus,
    DashboardStatistics, CaseTypeStatistics, UrgencyStatistics,
    ClientStatistics, TimelineDataPoint
)
from models.base import HealthStatus


class ElasticsearchService:
    """
    Comprehensive Elasticsearch service for document management.
    
    Provides document indexing, searching, aggregations, and analytics
    with proper error handling and performance monitoring.
    """
    
    def __init__(self):
        self.client: Optional[AsyncElasticsearch] = None
        self.index_name = settings.elasticsearch.index_name
        self.is_connected = False
        self._connection_pool_size = 10
        self._request_timeout = settings.elasticsearch.timeout
        
    async def initialize(self) -> None:
        """Initialize Elasticsearch connection and setup indices."""
        try:
            logger.info("🔍 Initializing Elasticsearch service...")
            
            # Create Elasticsearch client
            self.client = AsyncElasticsearch(
                hosts=settings.elasticsearch.hosts,
                timeout=self._request_timeout,
                max_retries=settings.elasticsearch.max_retries,
                retry_on_timeout=True,
                verify_certs=False,  # For development
                ssl_show_warn=False
            )
            
            # Test connection
            await self._test_connection()
            
            # Setup indices
            await self._setup_indices()
            
            self.is_connected = True
            logger.info("✅ Elasticsearch service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Elasticsearch: {e}")
            self.is_connected = False
            raise
    
    async def close(self) -> None:
        """Close Elasticsearch connection."""
        if self.client:
            try:
                await self.client.close()
                logger.info("✅ Elasticsearch connection closed")
            except Exception as e:
                logger.error(f"❌ Error closing Elasticsearch connection: {e}")
        
        self.is_connected = False
    
    async def _test_connection(self) -> None:
        """Test Elasticsearch connection."""
        try:
            info = await self.client.info()
            logger.info(f"🔍 Connected to Elasticsearch {info['version']['number']}")
        except Exception as e:
            logger.error(f"❌ Elasticsearch connection test failed: {e}")
            raise ConnectionError(f"Failed to connect to Elasticsearch: {e}")
    
    async def _setup_indices(self) -> None:
        """Setup Elasticsearch indices with proper mappings."""
        try:
            # Document index mapping
            document_mapping = {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "filename": {"type": "text", "analyzer": "standard"},
                        "content": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {
                                "keyword": {"type": "keyword", "ignore_above": 256}
                            }
                        },
                        "content_preview": {"type": "text"},
                        "case_type": {"type": "keyword"},
                        "urgency_level": {"type": "keyword"},
                        "document_type": {"type": "keyword"},
                        "client_name": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {
                                "keyword": {"type": "keyword", "ignore_above": 256}
                            }
                        },
                        "client_names": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "processed_at": {"type": "date"},
                        "date_created": {"type": "date"},
                        "deadline_date": {"type": "date"},
                        "tags": {"type": "keyword"},
                        "keywords": {"type": "keyword"},
                        "entities": {
                            "type": "nested",
                            "properties": {
                                "text": {"type": "text"},
                                "label": {"type": "keyword"},
                                "start": {"type": "integer"},
                                "end": {"type": "integer"},
                                "confidence": {"type": "float"}
                            }
                        },
                        "summary": {
                            "type": "object",
                            "properties": {
                                "sentences": {"type": "text"},
                                "keywords": {"type": "keyword"},
                                "topics": {"type": "keyword"},
                                "confidence": {"type": "float"}
                            }
                        },
                        "file_path": {"type": "keyword"},
                        "mime_type": {"type": "keyword"},
                        "file_hash": {"type": "keyword"},
                        "language": {"type": "keyword"},
                        "metrics": {
                            "type": "object",
                            "properties": {
                                "ocr_time_seconds": {"type": "float"},
                                "nlp_time_seconds": {"type": "float"},
                                "total_time_seconds": {"type": "float"},
                                "file_size_bytes": {"type": "long"},
                                "text_length": {"type": "integer"},
                                "confidence_scores": {"type": "object"}
                            }
                        }
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "legal_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "stop", "porter_stem"]
                            }
                        }
                    }
                }
            }
            
            # Create or update index
            index_exists = await self.client.indices.exists(index=self.index_name)
            if not index_exists:
                await self.client.indices.create(
                    index=self.index_name,
                    body=document_mapping
                )
                logger.info(f"✅ Created Elasticsearch index: {self.index_name}")
            else:
                logger.info(f"✅ Elasticsearch index already exists: {self.index_name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to setup Elasticsearch indices: {e}")
            raise
    
    async def index_document(self, document: Document) -> bool:
        """
        Index a document in Elasticsearch.
        
        Args:
            document: Document to index
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert document to dictionary suitable for Elasticsearch
            doc_dict = self._document_to_dict(document)
            
            # Index the document
            response = await self.client.index(
                index=self.index_name,
                id=str(document.id),
                body=doc_dict,
                refresh='wait_for'  # Ensure document is immediately searchable
            )
            
            logger.debug(f"✅ Indexed document {document.id}: {response['result']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to index document {document.id}: {e}")
            return False
    
    async def bulk_index_documents(self, documents: List[Document]) -> Tuple[int, int]:
        """
        Bulk index multiple documents.
        
        Args:
            documents: List of documents to index
            
        Returns:
            Tuple[int, int]: (successful_count, failed_count)
        """
        if not documents:
            return 0, 0
        
        try:
            # Prepare bulk operations
            bulk_operations = []
            for document in documents:
                bulk_operations.extend([
                    {
                        "index": {
                            "_index": self.index_name,
                            "_id": str(document.id)
                        }
                    },
                    self._document_to_dict(document)
                ])
            
            # Execute bulk operation
            response = await self.client.bulk(
                body=bulk_operations,
                refresh='wait_for'
            )
            
            # Count successes and failures
            successful = 0
            failed = 0
            
            for item in response['items']:
                if 'index' in item:
                    if item['index']['status'] in [200, 201]:
                        successful += 1
                    else:
                        failed += 1
                        logger.error(f"❌ Failed to index document: {item['index']}")
            
            logger.info(f"✅ Bulk indexed {successful} documents, {failed} failed")
            return successful, failed
            
        except Exception as e:
            logger.error(f"❌ Bulk index operation failed: {e}")
            return 0, len(documents)
    
    async def search_documents(self, search_request: DocumentSearchRequest) -> DocumentSearchResponse:
        """
        Search documents with advanced filtering and sorting.
        
        Args:
            search_request: Search criteria
            
        Returns:
            DocumentSearchResponse: Search results
        """
        try:
            # Build Elasticsearch query
            query = self._build_search_query(search_request)
            
            # Execute search
            response = await self.client.search(
                index=self.index_name,
                body=query,
                from_=search_request.offset,
                size=search_request.limit
            )
            
            # Process results
            documents = []
            for hit in response['hits']['hits']:
                doc_data = hit['_source']
                doc_data['id'] = hit['_id']
                
                # Convert to DocumentResponse
                document = DocumentResponse(**doc_data)
                documents.append(document)
            
            total = response['hits']['total']['value']
            
            return DocumentSearchResponse(
                documents=documents,
                total=total,
                limit=search_request.limit,
                offset=search_request.offset
            )
            
        except Exception as e:
            logger.error(f"❌ Document search failed: {e}")
            return DocumentSearchResponse(
                documents=[],
                total=0,
                limit=search_request.limit,
                offset=search_request.offset
            )
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a specific document by ID.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Optional[Document]: Document if found, None otherwise
        """
        try:
            response = await self.client.get(
                index=self.index_name,
                id=document_id
            )
            
            doc_data = response['_source']
            doc_data['id'] = response['_id']
            
            return Document(**doc_data)
            
        except NotFoundError:
            logger.warning(f"⚠️ Document not found: {document_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get document {document_id}: {e}")
            return None
    
    async def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a document in Elasticsearch.
        
        Args:
            document_id: Document identifier
            updates: Fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            response = await self.client.update(
                index=self.index_name,
                id=document_id,
                body={"doc": updates},
                refresh='wait_for'
            )
            
            logger.debug(f"✅ Updated document {document_id}: {response['result']}")
            return True
            
        except NotFoundError:
            logger.warning(f"⚠️ Document not found for update: {document_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to update document {document_id}: {e}")
            return False
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from Elasticsearch.
        
        Args:
            document_id: Document identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = await self.client.delete(
                index=self.index_name,
                id=document_id,
                refresh='wait_for'
            )
            
            logger.debug(f"✅ Deleted document {document_id}: {response['result']}")
            return True
            
        except NotFoundError:
            logger.warning(f"⚠️ Document not found for deletion: {document_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete document {document_id}: {e}")
            return False
    
    async def get_dashboard_statistics(self) -> DashboardStatistics:
        """
        Get comprehensive dashboard statistics.
        
        Returns:
            DashboardStatistics: Dashboard analytics data
        """
        try:
            # Build aggregation query
            aggs_query = {
                "query": {"match_all": {}},
                "size": 0,
                "aggs": {
                    "case_types": {
                        "terms": {"field": "case_type", "size": 20}
                    },
                    "urgency_levels": {
                        "terms": {"field": "urgency_level", "size": 10}
                    },
                    "top_clients": {
                        "terms": {"field": "client_name.keyword", "size": 10}
                    },
                    "high_priority": {
                        "filter": {
                            "terms": {"urgency_level": ["high", "critical"]}
                        }
                    },
                    "critical_priority": {
                        "filter": {"term": {"urgency_level": "critical"}}
                    },
                    "upload_timeline": {
                        "date_histogram": {
                            "field": "created_at",
                            "calendar_interval": "day",
                            "format": "yyyy-MM-dd"
                        },
                        "aggs": {
                            "case_types": {
                                "terms": {"field": "case_type", "size": 10}
                            }
                        }
                    }
                }
            }
            
            response = await self.client.search(
                index=self.index_name,
                body=aggs_query
            )
            
            total_docs = response['hits']['total']['value']
            aggs = response['aggregations']
            
            # Process case type distribution
            case_type_stats = []
            for bucket in aggs['case_types']['buckets']:
                case_type_stats.append(CaseTypeStatistics(
                    case_type=bucket['key'],
                    count=bucket['doc_count'],
                    percentage=(bucket['doc_count'] / total_docs * 100) if total_docs > 0 else 0
                ))
            
            # Process urgency distribution
            urgency_stats = []
            for bucket in aggs['urgency_levels']['buckets']:
                urgency_stats.append(UrgencyStatistics(
                    urgency_level=bucket['key'],
                    count=bucket['doc_count'],
                    percentage=(bucket['doc_count'] / total_docs * 100) if total_docs > 0 else 0
                ))
            
            # Process client statistics
            client_stats = []
            for bucket in aggs['top_clients']['buckets']:
                if bucket['key']:  # Skip empty client names
                    client_stats.append(ClientStatistics(
                        client_name=bucket['key'],
                        document_count=bucket['doc_count'],
                        case_types=[],  # Could be expanded with sub-aggregation
                        latest_document=datetime.utcnow()  # Could be fetched with sub-aggregation
                    ))
            
            # Process timeline data
            timeline_data = []
            for bucket in aggs['upload_timeline']['buckets']:
                case_type_breakdown = {}
                for ct_bucket in bucket['case_types']['buckets']:
                    case_type_breakdown[ct_bucket['key']] = ct_bucket['doc_count']
                
                timeline_data.append(TimelineDataPoint(
                    date=datetime.fromisoformat(bucket['key_as_string']).date(),
                    count=bucket['doc_count'],
                    case_types=case_type_breakdown
                ))
            
            return DashboardStatistics(
                total_documents=total_docs,
                high_priority_count=aggs['high_priority']['doc_count'],
                critical_priority_count=aggs['critical_priority']['doc_count'],
                active_clients=len(client_stats),
                case_type_distribution=case_type_stats,
                urgency_distribution=urgency_stats,
                top_clients=client_stats[:5],
                upload_timeline=timeline_data[-30:],  # Last 30 days
                processing_stats={
                    "avg_processing_time": 0,  # Could be calculated from metrics
                    "success_rate": 100  # Could be calculated from status field
                },
                system_health={
                    "elasticsearch": "healthy",
                    "response_time_ms": 50
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to get dashboard statistics: {e}")
            # Return empty statistics on error
            return DashboardStatistics(
                total_documents=0,
                high_priority_count=0,
                critical_priority_count=0,
                active_clients=0,
                case_type_distribution=[],
                urgency_distribution=[],
                top_clients=[],
                upload_timeline=[],
                processing_stats={},
                system_health={"elasticsearch": "error"}
            )
    
    async def health_check(self) -> HealthStatus:
        """
        Perform health check on Elasticsearch service.
        
        Returns:
            HealthStatus: Service health status
        """
        start_time = datetime.utcnow()
        
        try:
            # Test basic connectivity
            await self.client.ping()
            
            # Test cluster health
            cluster_health = await self.client.cluster.health()
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return HealthStatus(
                service="elasticsearch",
                status="healthy" if cluster_health['status'] in ['green', 'yellow'] else "unhealthy",
                response_time_ms=response_time,
                details={
                    "cluster_status": cluster_health['status'],
                    "number_of_nodes": cluster_health['number_of_nodes'],
                    "active_shards": cluster_health['active_shards'],
                    "index_exists": await self.client.indices.exists(index=self.index_name)
                }
            )
            
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"❌ Elasticsearch health check failed: {e}")
            
            return HealthStatus(
                service="elasticsearch",
                status="unhealthy",
                response_time_ms=response_time,
                details={"error": str(e)}
            )
    
    def is_connected(self) -> bool:
        """Check if service is connected."""
        return self.is_connected
    
    def _document_to_dict(self, document: Document) -> Dict[str, Any]:
        """Convert Document model to Elasticsearch dictionary."""
        doc_dict = document.dict(exclude={'id'})
        
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'updated_at', 'processed_at']:
            if doc_dict.get(field):
                if isinstance(doc_dict[field], datetime):
                    doc_dict[field] = doc_dict[field].isoformat()
        
        # Convert date objects to ISO strings
        for field in ['date_created', 'deadline_date']:
            if doc_dict.get(field):
                if isinstance(doc_dict[field], date):
                    doc_dict[field] = doc_dict[field].isoformat()
        
        return doc_dict
    
    def _build_search_query(self, search_request: DocumentSearchRequest) -> Dict[str, Any]:
        """Build Elasticsearch query from search request."""
        query = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            },
            "sort": [
                {search_request.sort_by: {"order": search_request.sort_order}}
            ]
        }
        
        # Text search
        if search_request.query:
            query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": search_request.query,
                    "fields": [
                        "content^2",
                        "filename^1.5",
                        "client_name^1.5",
                        "tags",
                        "keywords"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        
        # Case type filter
        if search_request.case_types:
            query["query"]["bool"]["filter"].append({
                "terms": {"case_type": search_request.case_types}
            })
        
        # Urgency level filter
        if search_request.urgency_levels:
            query["query"]["bool"]["filter"].append({
                "terms": {"urgency_level": search_request.urgency_levels}
            })
        
        # Client names filter
        if search_request.client_names:
            query["query"]["bool"]["filter"].append({
                "terms": {"client_name.keyword": search_request.client_names}
            })
        
        # Tags filter
        if search_request.tags:
            query["query"]["bool"]["filter"].append({
                "terms": {"tags": search_request.tags}
            })
        
        # Status filter
        if search_request.status:
            query["query"]["bool"]["filter"].append({
                "terms": {"status": search_request.status}
            })
        
        # Date range filter
        if search_request.date_from or search_request.date_to:
            date_range = {}
            if search_request.date_from:
                date_range["gte"] = search_request.date_from.isoformat()
            if search_request.date_to:
                date_range["lte"] = search_request.date_to.isoformat()
            
            query["query"]["bool"]["filter"].append({
                "range": {"created_at": date_range}
            })
        
        # If no must clauses, match all
        if not query["query"]["bool"]["must"]:
            query["query"]["bool"]["must"].append({"match_all": {}})
        
        return query


# Global Elasticsearch service instance
elasticsearch_service = ElasticsearchService() 