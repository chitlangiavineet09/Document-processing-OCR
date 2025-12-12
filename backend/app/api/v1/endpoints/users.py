"""User profile endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging
from app.core.auth import get_current_user
from app.services.database import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user_profile(user: dict = Depends(get_current_user)):
    """
    Get current user's profile including role information.
    """
    user_id = user["user_id"]
    
    try:
        supabase = get_supabase_client()
        
        # Get profile with role information
        profile_result = supabase.table("profiles").select(
            "id, email, full_name, role_id, deleted_at"
        ).eq("id", user_id).single().execute()
        
        if not profile_result.data:
            # Profile doesn't exist yet, return basic info from JWT
            return {
                "id": user_id,
                "email": user.get("email"),
                "full_name": None,
                "role": user.get("user_role", "user"),
                "is_admin": user.get("is_admin", False),
                "deleted_at": None
            }
        
        profile = profile_result.data
        role_id = profile.get("role_id")
        
        # Get role name if role_id exists
        role_name = "user"
        if role_id:
            try:
                role_result = supabase.table("roles").select("name").eq("id", role_id).single().execute()
                if role_result.data:
                    role_name = role_result.data.get("name", "user")
            except Exception as e:
                logger.warning(f"Failed to load role for user {user_id}: {str(e)}")
        
        return {
            "id": profile["id"],
            "email": profile.get("email") or user.get("email"),
            "full_name": profile.get("full_name"),
            "role": role_name,
            "is_admin": role_name == "admin",
            "deleted_at": profile.get("deleted_at")
        }
        
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}", exc_info=True)
        # Fallback to basic info from JWT
        return {
            "id": user_id,
            "email": user.get("email"),
            "full_name": None,
            "role": user.get("user_role", "user"),
            "is_admin": user.get("is_admin", False),
            "deleted_at": None
        }

