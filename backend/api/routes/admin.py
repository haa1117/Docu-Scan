"""
DocuScan Administration API Routes

This module provides administration endpoints for system management,
configuration, and monitoring of the DocuScan system.
"""

from datetime import datetime
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from loguru import logger

from backend.config import settings
from backend.models.base import SystemHealth, MetricsInfo


# Initialize router
router = APIRouter()


class SystemConfigRequest(BaseModel):
    """System configuration update request."""
    maintenance_mode: bool = None
    max_file_size_mb: int = None
    allowed_file_types: List[str] = None
    auto_classification_enabled: bool = None


class SystemConfigResponse(BaseModel):
    """System configuration response."""
    maintenance_mode: bool
    max_file_size_mb: int
    allowed_file_types: List[str]
    auto_classification_enabled: bool
    updated_at: datetime


@router.get("/config", response_model=SystemConfigResponse)
async def get_system_config():
    """
    Get current system configuration.
    
    Returns:
        SystemConfigResponse: Current system configuration
    """
    try:
        logger.info("⚙️ Retrieving system configuration")
        
        config = SystemConfigResponse(
            maintenance_mode=False,
            max_file_size_mb=settings.file_upload.max_file_size_mb,
            allowed_file_types=settings.file_upload.allowed_extensions,
            auto_classification_enabled=True,
            updated_at=datetime.utcnow()
        )
        
        logger.info("✅ System configuration retrieved")
        return config
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve system configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system configuration"
        )


@router.put("/config", response_model=SystemConfigResponse)
async def update_system_config(config_request: SystemConfigRequest):
    """
    Update system configuration.
    
    Args:
        config_request: Configuration updates
        
    Returns:
        SystemConfigResponse: Updated system configuration
    """
    try:
        logger.info("⚙️ Updating system configuration")
        
        # In production, this would update the actual configuration
        # For demo, return the updated values
        
        config = SystemConfigResponse(
            maintenance_mode=config_request.maintenance_mode if config_request.maintenance_mode is not None else False,
            max_file_size_mb=config_request.max_file_size_mb or settings.file_upload.max_file_size_mb,
            allowed_file_types=config_request.allowed_file_types or settings.file_upload.allowed_extensions,
            auto_classification_enabled=config_request.auto_classification_enabled if config_request.auto_classification_enabled is not None else True,
            updated_at=datetime.utcnow()
        )
        
        logger.info("✅ System configuration updated")
        return config
        
    except Exception as e:
        logger.error(f"❌ Failed to update system configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update system configuration"
        )


@router.get("/system/status", response_model=Dict[str, Any])
async def get_system_status():
    """
    Get comprehensive system status.
    
    Returns:
        Dict[str, Any]: System status information
    """
    try:
        logger.info("📊 Retrieving system status")
        
        status_info = {
            "system": {
                "status": "operational",
                "uptime_seconds": 3600,
                "version": settings.api.version,
                "environment": settings.environment
            },
            "services": {
                "elasticsearch": "healthy",
                "nlp": "healthy",
                "ocr": "healthy"
            },
            "resources": {
                "cpu_usage_percent": 25.5,
                "memory_usage_percent": 45.2,
                "disk_usage_percent": 60.0
            },
            "stats": {
                "total_documents": 1000,
                "documents_processed_today": 50,
                "active_users": 5,
                "avg_processing_time_seconds": 8.5
            }
        }
        
        logger.info("✅ System status retrieved")
        return status_info
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )


@router.post("/system/maintenance", response_model=Dict[str, str])
async def toggle_maintenance_mode(enable: bool):
    """
    Toggle system maintenance mode.
    
    Args:
        enable: Whether to enable maintenance mode
        
    Returns:
        Dict[str, str]: Maintenance mode status
    """
    try:
        mode = "enabled" if enable else "disabled"
        logger.info(f"🔧 Setting maintenance mode to: {mode}")
        
        # In production, this would actually toggle maintenance mode
        
        logger.info(f"✅ Maintenance mode {mode}")
        
        return {
            "maintenance_mode": mode,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Maintenance mode has been {mode}"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to toggle maintenance mode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle maintenance mode"
        )


@router.get("/logs", response_model=Dict[str, Any])
async def get_system_logs(
    level: str = "INFO",
    limit: int = 100,
    since: str = None
):
    """
    Get system logs.
    
    Args:
        level: Log level filter
        limit: Maximum number of log entries
        since: ISO timestamp to filter logs since
        
    Returns:
        Dict[str, Any]: System logs
    """
    try:
        logger.info(f"📋 Retrieving system logs: level={level}, limit={limit}")
        
        # Mock log entries - in production, read from actual log files
        mock_logs = [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "level": "INFO",
                "service": "api",
                "message": "Document uploaded successfully",
                "details": {"document_id": "123", "filename": "contract.pdf"}
            },
            {
                "timestamp": "2024-01-01T12:01:00Z",
                "level": "INFO",
                "service": "nlp",
                "message": "Document classification completed",
                "details": {"document_id": "123", "case_type": "corporate"}
            },
            {
                "timestamp": "2024-01-01T12:02:00Z",
                "level": "WARNING",
                "service": "ocr",
                "message": "OCR confidence below threshold",
                "details": {"document_id": "124", "confidence": 0.65}
            }
        ]
        
        logs_response = {
            "logs": mock_logs[:limit],
            "total_count": len(mock_logs),
            "level_filter": level,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Retrieved {len(mock_logs)} log entries")
        return logs_response
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve system logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system logs"
        )


@router.post("/cache/clear", response_model=Dict[str, str])
async def clear_system_cache():
    """
    Clear system caches.
    
    Returns:
        Dict[str, str]: Cache clear confirmation
    """
    try:
        logger.info("🧹 Clearing system caches")
        
        # In production, this would clear various caches:
        # - NLP model cache
        # - OCR processing cache
        # - Search result cache
        # - API response cache
        
        logger.info("✅ System caches cleared")
        
        return {
            "status": "success",
            "message": "System caches have been cleared",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to clear system caches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear system caches"
        )


@router.get("/users", response_model=Dict[str, Any])
async def get_system_users():
    """
    Get system users and their activity.
    
    Returns:
        Dict[str, Any]: User information
    """
    try:
        logger.info("👥 Retrieving system users")
        
        # Mock user data - in production, query from user database
        users_data = {
            "users": [
                {
                    "username": "admin",
                    "role": "administrator",
                    "last_login": "2024-01-01T10:00:00Z",
                    "documents_uploaded": 150,
                    "status": "active"
                },
                {
                    "username": "lawyer1",
                    "role": "user",
                    "last_login": "2024-01-01T09:30:00Z",
                    "documents_uploaded": 75,
                    "status": "active"
                },
                {
                    "username": "paralegal1",
                    "role": "user",
                    "last_login": "2024-01-01T08:45:00Z",
                    "documents_uploaded": 25,
                    "status": "active"
                }
            ],
            "total_users": 3,
            "active_users": 3,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Retrieved {users_data['total_users']} users")
        return users_data
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve system users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system users"
        ) 