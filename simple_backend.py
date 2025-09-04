#!/usr/bin/env python3
"""
Simple DocuScan Backend Server

A minimal FastAPI backend to serve the DocuScan dashboard while the main
backend container is being fixed.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime
from elasticsearch import AsyncElasticsearch

app = FastAPI(
    title="DocuScan API",
    description="Legal Document Classification System",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Elasticsearch client
es_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize Elasticsearch connection on startup."""
    global es_client
    try:
        es_client = AsyncElasticsearch("http://localhost:9200")
        await es_client.info()
        print("✅ Connected to Elasticsearch")
    except Exception as e:
        print(f"❌ Failed to connect to Elasticsearch: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Close Elasticsearch connection on shutdown."""
    global es_client
    if es_client:
        await es_client.close()

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "DocuScan API is running", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        if es_client:
            await es_client.info()
            es_status = "healthy"
        else:
            es_status = "unhealthy"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "api": "healthy",
                "elasticsearch": es_status
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.get("/api/documents/search")
async def search_documents(
    q: Optional[str] = Query(None, description="Search query"),
    case_type: Optional[str] = Query(None, description="Filter by case type"),
    urgency_level: Optional[str] = Query(None, description="Filter by urgency level"),
    client_name: Optional[str] = Query(None, description="Filter by client name"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size")
):
    """Search documents with filters."""
    try:
        if not es_client:
            raise HTTPException(status_code=503, detail="Elasticsearch not available")
        
        # Build query
        query = {"match_all": {}}
        filters = []
        
        if q and q.strip():
            query = {"multi_match": {"query": q, "fields": ["content", "filename", "client_name"]}}
        
        if case_type and case_type.strip():
            filters.append({"term": {"case_type": case_type}})
        
        if urgency_level and urgency_level.strip():
            filters.append({"term": {"urgency_level": urgency_level}})
        
        if client_name and client_name.strip():
            filters.append({"match": {"client_name": client_name}})
        
        # Build search body
        search_body = {
            "query": {
                "bool": {
                    "must": [query],
                    "filter": filters
                }
            },
            "from": (page - 1) * size,
            "size": size,
            "sort": [{"created_at": {"order": "desc"}}]
        }
        
        response = await es_client.search(
            index="docuscan_documents",
            body=search_body
        )
        
        # Format results
        documents = []
        for hit in response["hits"]["hits"]:
            doc = hit["_source"]
            doc["id"] = hit["_id"]
            doc["score"] = hit["_score"]
            documents.append(doc)
        
        return {
            "documents": documents,
            "total": response["hits"]["total"]["value"],
            "page": page,
            "size": size,
            "total_pages": (response["hits"]["total"]["value"] + size - 1) // size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/documents/{document_id}")
async def get_document(document_id: str):
    """Get a specific document by ID."""
    try:
        if not es_client:
            raise HTTPException(status_code=503, detail="Elasticsearch not available")
        
        response = await es_client.get(
            index="docuscan_documents",
            id=document_id
        )
        
        document = response["_source"]
        document["id"] = response["_id"]
        
        return document
        
    except Exception as e:
        if "not_found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Document not found")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")

@app.get("/api/dashboard/statistics")
async def get_dashboard_statistics():
    """Get dashboard statistics."""
    try:
        if not es_client:
            raise HTTPException(status_code=503, detail="Elasticsearch not available")
        
        # Get total documents
        count_response = await es_client.count(index="docuscan_documents")
        total_documents = count_response["count"]
        
        # Get aggregations
        agg_response = await es_client.search(
            index="docuscan_documents",
            body={
                "size": 0,
                "aggs": {
                    "case_types": {"terms": {"field": "case_type", "size": 20}},
                    "urgency_levels": {"terms": {"field": "urgency_level"}},
                    "clients": {"terms": {"field": "client_name.keyword", "size": 10}},
                    "recent_documents": {
                        "date_histogram": {
                            "field": "created_at",
                            "calendar_interval": "day",
                            "order": {"_key": "desc"}
                        }
                    }
                }
            }
        )
        
        aggs = agg_response["aggregations"]
        
        # Count high/critical priority documents
        high_priority = sum(bucket["doc_count"] for bucket in aggs["urgency_levels"]["buckets"] 
                           if bucket["key"] in ["high", "critical"])
        
        critical_priority = sum(bucket["doc_count"] for bucket in aggs["urgency_levels"]["buckets"] 
                               if bucket["key"] == "critical")
        
        return {
            "total_documents": total_documents,
            "high_priority_count": high_priority,
            "critical_priority_count": critical_priority,
            "active_clients": len(aggs["clients"]["buckets"]),
            "case_type_distribution": [
                {"case_type": bucket["key"], "count": bucket["doc_count"]} 
                for bucket in aggs["case_types"]["buckets"]
            ],
            "urgency_distribution": [
                {"urgency_level": bucket["key"], "count": bucket["doc_count"]} 
                for bucket in aggs["urgency_levels"]["buckets"]
            ],
            "top_clients": [
                {"client_name": bucket["key"], "document_count": bucket["doc_count"]} 
                for bucket in aggs["clients"]["buckets"]
            ],
            "timeline": [
                {"date": bucket["key_as_string"], "count": bucket["doc_count"]} 
                for bucket in aggs["recent_documents"]["buckets"]
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@app.get("/api/documents")
async def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """List all documents with pagination."""
    return await search_documents(page=page, size=size)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 