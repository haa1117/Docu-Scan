"""
DocuScan Authentication API Routes

This module provides authentication endpoints for the DocuScan system
including login, token validation, and user management.
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from loguru import logger

from backend.config import settings


# Initialize router and security
router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest):
    """
    Authenticate user and return access token.
    
    Args:
        login_request: User credentials
        
    Returns:
        TokenResponse: Access token information
    """
    try:
        logger.info(f"🔐 Login attempt for user: {login_request.username}")
        
        # Demo authentication - in production, validate against a database
        if login_request.username == "admin" and login_request.password == "admin123":
            # Generate demo token
            access_token = "demo-token"
            expires_in = settings.security.access_token_expire_minutes * 60
            
            logger.info(f"✅ Login successful for user: {login_request.username}")
            
            return TokenResponse(
                access_token=access_token,
                expires_in=expires_in
            )
        
        else:
            logger.warning(f"❌ Login failed for user: {login_request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


@router.post("/validate", response_model=Dict[str, Any])
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate authentication token.
    
    Args:
        credentials: Bearer token credentials
        
    Returns:
        Dict[str, Any]: User information
    """
    try:
        logger.info("🔍 Validating authentication token")
        
        # Demo validation - in production, validate JWT token
        if credentials.credentials == "demo-token":
            user_info = {
                "username": "admin",
                "role": "administrator",
                "permissions": ["read", "write", "admin"],
                "expires_at": (datetime.utcnow() + timedelta(minutes=30)).isoformat()
            }
            
            logger.info("✅ Token validation successful")
            return {
                "valid": True,
                "user": user_info
            }
        
        else:
            logger.warning("❌ Invalid token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token validation service error"
        )


@router.post("/logout", response_model=Dict[str, str])
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout user and invalidate token.
    
    Args:
        credentials: Bearer token credentials
        
    Returns:
        Dict[str, str]: Logout confirmation
    """
    try:
        logger.info("🚪 User logout")
        
        # In production, invalidate the token in a blacklist or database
        # For demo, just return success
        
        logger.info("✅ Logout successful")
        return {
            "message": "Logout successful",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout service error"
        ) 