from fastapi import Request, HTTPException, status, Depends
from jose import jwt, JWTError
from typing import Optional, Dict
from app.core.config import settings
from app.services.database import get_supabase_client
import logging

logger = logging.getLogger(__name__)


async def verify_supabase_token(request: Request) -> Dict[str, str]:
    """
    Verify Supabase JWT token and return user information.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary containing user_id, email, and token
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Missing or invalid authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Verify token signature and decode
        # Supabase uses HS256 algorithm and the JWT secret
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
            }
        )
        
        # Extract user info from token
        user_id = payload.get("sub")  # Supabase user ID (UUID)
        email = payload.get("email")
        role = payload.get("role", "authenticated")
        
        if not user_id:
            logger.error("Token missing user ID")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        logger.info(f"Authenticated user: {user_id}")
        
        # Load user role from profiles table and check if user is soft deleted
        user_role_name = None
        is_admin = False
        is_deleted = False
        try:
            supabase = get_supabase_client()
            # Get profile with role_id and deleted_at
            profile_result = supabase.table("profiles").select(
                "id, email, full_name, role_id, deleted_at"
            ).eq("id", user_id).single().execute()
            
            if profile_result.data:
                profile = profile_result.data
                
                # Check if user is soft deleted
                if profile.get("deleted_at"):
                    is_deleted = True
                    logger.warning(f"Soft-deleted user {user_id} attempted to authenticate")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Your account has been deactivated. Please contact your administrator."
                    )
                
                if profile.get("role_id"):
                    role_id = profile["role_id"]
                    
                    # Get role name from roles table
                    role_result = supabase.table("roles").select("name").eq("id", role_id).single().execute()
                    
                    if role_result.data:
                        user_role_name = role_result.data.get("name", "user")
                        is_admin = user_role_name == "admin"
                        logger.info(f"User {user_id} has role: {user_role_name}")
        except HTTPException:
            # Re-raise HTTP exceptions (like deleted user)
            raise
        except Exception as e:
            logger.warning(f"Failed to load user role from profiles: {str(e)}")
            # Continue with default role if profile lookup fails
            user_role_name = "user"
        
        return {
            "user_id": user_id,
            "email": email,
            "role": role,  # JWT role (usually "authenticated")
            "user_role": user_role_name or "user",  # Database role from profiles table
            "is_admin": is_admin,
            "token": token
        }
        
    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(request: Request = None) -> Dict[str, str]:
    """
    Dependency function to get current authenticated user.
    Can be used in FastAPI route dependencies.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            user_id = user["user_id"]
    """
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Request object not available"
        )
    return await verify_supabase_token(request)


async def get_current_user_optional(request: Request) -> Optional[Dict[str, str]]:
    """
    Optional authentication - returns None if no token provided.
    Useful for routes that work with or without authentication.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    try:
        return await verify_supabase_token(request)
    except HTTPException:
        return None


async def get_admin_user(user: Dict = Depends(get_current_user)) -> Dict[str, str]:
    """
    Dependency function to verify user is admin.
    Raises 403 if user is not admin.
    
    Usage:
        @app.get("/admin/route")
        async def admin_route(admin: dict = Depends(get_admin_user)):
            # Only admins can access this
    """
    if not user.get("is_admin", False):
        logger.warning(f"Non-admin user {user.get('user_id')} attempted to access admin route")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

