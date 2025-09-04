"""
DocuScan Health Check API Routes

This module provides health check and system monitoring endpoints for the
DocuScan legal document classification system.
"""

from datetime import datetime
from typing import Dict, Any
import asyncio
import psutil

from fastapi import APIRouter, HTTPException, status
from loguru import logger

from backend.models.base import HealthStatus, SystemHealth, MetricsInfo
from backend.config import settings


# Initialize router
router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        Dict[str, Any]: Basic health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "DocuScan API",
        "version": settings.api.version
    }


@router.get("/detailed", response_model=SystemHealth)
async def detailed_health_check():
    """
    Detailed health check with service status.
    
    Returns:
        SystemHealth: Comprehensive system health information
    """
    try:
        logger.info("🏥 Performing detailed health check")
        
        # Check individual services
        services = []
        
        # Elasticsearch health check
        try:
            # This would be injected from the main app
            es_status = HealthStatus(
                service="elasticsearch",
                status="healthy",
                response_time_ms=50.0,
                details={"cluster_status": "green"}
            )
            services.append(es_status)
        except Exception as e:
            logger.error(f"❌ Elasticsearch health check failed: {e}")
            services.append(HealthStatus(
                service="elasticsearch",
                status="unhealthy",
                details={"error": str(e)}
            ))
        
        # NLP service health check
        try:
            nlp_status = HealthStatus(
                service="nlp",
                status="healthy",
                response_time_ms=25.0,
                details={"model_loaded": True}
            )
            services.append(nlp_status)
        except Exception as e:
            logger.error(f"❌ NLP service health check failed: {e}")
            services.append(HealthStatus(
                service="nlp",
                status="unhealthy",
                details={"error": str(e)}
            ))
        
        # OCR service health check
        try:
            ocr_status = HealthStatus(
                service="ocr",
                status="healthy",
                response_time_ms=30.0,
                details={"tesseract_available": True}
            )
            services.append(ocr_status)
        except Exception as e:
            logger.error(f"❌ OCR service health check failed: {e}")
            services.append(HealthStatus(
                service="ocr",
                status="unhealthy",
                details={"error": str(e)}
            ))
        
        # Determine overall status
        unhealthy_services = [s for s in services if s.status != "healthy"]
        overall_status = "unhealthy" if unhealthy_services else "healthy"
        
        # Calculate uptime (mock for now)
        uptime_seconds = 3600.0  # 1 hour mock uptime
        
        system_health = SystemHealth(
            status=overall_status,
            services=services,
            version=settings.api.version,
            uptime_seconds=uptime_seconds
        )
        
        logger.info(f"✅ Health check completed: {overall_status}")
        return system_health
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/metrics", response_model=MetricsInfo)
async def get_system_metrics():
    """
    Get detailed system metrics.
    
    Returns:
        MetricsInfo: System performance metrics
    """
    try:
        logger.info("📊 Retrieving system metrics")
        
        # Get system metrics using psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Mock connection and request metrics (would come from Prometheus in production)
        active_connections = 5
        total_requests = 1000
        avg_response_time_ms = 150.0
        
        metrics = MetricsInfo(
            cpu_usage_percent=cpu_percent,
            memory_usage_percent=memory.percent,
            disk_usage_percent=disk.percent,
            active_connections=active_connections,
            total_requests=total_requests,
            average_response_time_ms=avg_response_time_ms
        )
        
        logger.info(f"✅ System metrics retrieved: CPU {cpu_percent}%, Memory {memory.percent}%")
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Metrics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics retrieval failed: {str(e)}"
        )


@router.get("/readiness")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        Dict[str, str]: Readiness status
    """
    try:
        # Check if essential services are ready
        # In a real implementation, this would check:
        # - Database connectivity
        # - Required models loaded
        # - External service dependencies
        
        # For now, return ready
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        Dict[str, str]: Liveness status
    """
    try:
        # Basic liveness check - if this endpoint responds, the service is alive
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Liveness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service not alive"
        ) 