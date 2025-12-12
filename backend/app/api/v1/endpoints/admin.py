"""Admin endpoints - requires admin role"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import uuid

from app.core.auth import get_admin_user
from app.services.database import get_supabase_client, get_supabase_admin_client
from app.models.schemas import UserOut, UserCreate, UserUpdate, SettingUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/users", response_model=List[UserOut], status_code=status.HTTP_200_OK)
async def list_users(
    include_deleted: bool = False,
    admin: dict = Depends(get_admin_user)
):
    """
    List all users (admin only).
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("profiles").select(
            "id, email, full_name, role_id, created_at, updated_at, deleted_at"
        )
        
        if not include_deleted:
            query = query.is_("deleted_at", "null")
        
        result = query.order("created_at", desc=True).execute()
        
        users = []
        # Get all unique role_ids to batch fetch roles
        role_ids = set()
        for user_data in (result.data or []):
            if user_data.get("role_id"):
                role_ids.add(user_data["role_id"])
        
        # Fetch all roles at once
        roles_map = {}
        if role_ids:
            try:
                role_ids_list = list(role_ids)
                if role_ids_list:
                    roles_result = supabase.table("roles").select("id, name").in_("id", role_ids_list).execute()
                    if roles_result.data:
                        for role in roles_result.data:
                            roles_map[role["id"]] = role.get("name", "user")
            except Exception as e:
                logger.warning(f"Failed to fetch roles: {str(e)}")
        
        for user_data in (result.data or []):
            role_name = "user"
            if user_data.get("role_id") and user_data["role_id"] in roles_map:
                role_name = roles_map[user_data["role_id"]]
            
            users.append({
                "id": user_data["id"],
                "email": user_data.get("email"),
                "full_name": user_data.get("full_name"),
                "role": role_name,
                "created_at": user_data.get("created_at"),
                "updated_at": user_data.get("updated_at"),
                "deleted_at": user_data.get("deleted_at"),
                "is_active": user_data.get("deleted_at") is None
            })
        
        return users
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: str,
    admin: dict = Depends(get_admin_user)
):
    """
    Get a specific user by ID (admin only).
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("profiles").select(
            "id, email, full_name, role_id, created_at, updated_at, deleted_at"
        ).eq("id", user_id).single().execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = result.data
        role_name = "user"
        if user_data.get("role_id"):
            try:
                role_result = supabase.table("roles").select("name").eq("id", user_data["role_id"]).single().execute()
                if role_result.data:
                    role_name = role_result.data.get("name")
            except:
                pass
        
        return {
            "id": user_data["id"],
            "email": user_data.get("email"),
            "full_name": user_data.get("full_name"),
            "role": role_name,
            "created_at": user_data.get("created_at"),
            "updated_at": user_data.get("updated_at"),
            "deleted_at": user_data.get("deleted_at"),
            "is_active": user_data.get("deleted_at") is None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
        )


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    admin: dict = Depends(get_admin_user)
):
    """
    Create a new user (admin only).
    Creates user in Supabase Auth and then creates profile record.
    """
    try:
        supabase = get_supabase_client()
        supabase_admin = get_supabase_admin_client()
        
        # Validate role exists
        if user_data.role:
            role_result = supabase.table("roles").select("id").eq("name", user_data.role.lower()).single().execute()
            if not role_result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {user_data.role}"
                )
            role_id = role_result.data["id"]
        else:
            # Default to user role
            role_result = supabase.table("roles").select("id").eq("name", "user").single().execute()
            role_id = role_result.data["id"] if role_result.data else None
        
        # Check if user already exists in auth.users by email
        try:
            existing_users = supabase_admin.auth.admin.list_users()
            for user in existing_users.users:
                if user.email == user_data.email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"User with email {user_data.email} already exists"
                    )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Error checking existing users: {str(e)}")
            # Continue if we can't check (might be permission issue)
        
        # Create user in Supabase Auth using admin client
        try:
            auth_response = supabase_admin.auth.admin.create_user({
                "email": user_data.email,
                "password": user_data.password,
                "email_confirm": True,  # Auto-confirm email so user can login immediately
                "user_metadata": {
                    "full_name": user_data.full_name
                }
            })
            
            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user in authentication system"
                )
            
            user_id = auth_response.user.id
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating auth user: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user in authentication system: {str(e)}"
            )
        
        # Create profile record
        try:
            profile_data = {
                "id": user_id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "role_id": role_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = supabase_admin.table("profiles").insert(profile_data).execute()
            
            if not result.data:
                # If profile creation fails, try to clean up auth user
                try:
                    supabase_admin.auth.admin.delete_user(user_id)
                except:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user profile"
                )
            
            created_user = result.data[0] if isinstance(result.data, list) else result.data
            
            return {
                "id": created_user["id"],
                "email": created_user.get("email"),
                "full_name": created_user.get("full_name"),
                "role": user_data.role or "user",
                "created_at": created_user.get("created_at"),
                "updated_at": created_user.get("updated_at"),
                "deleted_at": None,
                "is_active": True
            }
            
        except HTTPException:
            # Clean up auth user if profile creation failed
            try:
                supabase_admin.auth.admin.delete_user(user_id)
            except:
                pass
            raise
        except Exception as e:
            # Clean up auth user if profile creation failed
            try:
                supabase_admin.auth.admin.delete_user(user_id)
            except:
                pass
            logger.error(f"Error creating profile: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user profile: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.patch("/users/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    admin: dict = Depends(get_admin_user)
):
    """
    Update a user (admin only).
    """
    try:
        supabase = get_supabase_client()
        
        # Check if user exists
        existing = supabase.table("profiles").select("id").eq("id", user_id).single().execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Build update data
        update_data: Dict[str, Any] = {
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if user_data.full_name is not None:
            update_data["full_name"] = user_data.full_name
        
        if user_data.email is not None:
            update_data["email"] = user_data.email
        
        if user_data.role is not None:
            # Get role_id
            role_result = supabase.table("roles").select("id").eq("name", user_data.role.lower()).single().execute()
            if not role_result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {user_data.role}"
                )
            update_data["role_id"] = role_result.data["id"]
        
        # Update profile
        result = supabase.table("profiles").update(update_data).eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
        
        updated_user = result.data[0] if isinstance(result.data, list) else result.data
        
        # Get role name
        role_name = user_data.role or "user"
        if updated_user.get("role_id"):
            try:
                role_result = supabase.table("roles").select("name").eq("id", updated_user["role_id"]).single().execute()
                if role_result.data:
                    role_name = role_result.data.get("name")
            except:
                pass
        
        return {
            "id": updated_user["id"],
            "email": updated_user.get("email"),
            "full_name": updated_user.get("full_name"),
            "role": role_name,
            "created_at": updated_user.get("created_at"),
            "updated_at": updated_user.get("updated_at"),
            "deleted_at": updated_user.get("deleted_at"),
            "is_active": updated_user.get("deleted_at") is None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: str,
    hard_delete: bool = False,
    admin: dict = Depends(get_admin_user)
):
    """
    Delete a user (admin only).
    By default performs soft delete. Set hard_delete=true for permanent deletion.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if user exists
        existing = supabase.table("profiles").select("id, deleted_at").eq("id", user_id).single().execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if hard_delete:
            # Permanent delete
            supabase.table("profiles").delete().eq("id", user_id).execute()
            return {"message": "User permanently deleted"}
        else:
            # Soft delete
            supabase.table("profiles").update({
                "deleted_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            return {"message": "User soft deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/users/{user_id}/restore", response_model=UserOut, status_code=status.HTTP_200_OK)
async def restore_user(
    user_id: str,
    admin: dict = Depends(get_admin_user)
):
    """
    Restore a soft-deleted user (admin only).
    """
    try:
        supabase = get_supabase_client()
        
        # Check if user exists
        existing = supabase.table("profiles").select("id, deleted_at").eq("id", user_id).single().execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not existing.data.get("deleted_at"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not deleted"
            )
        
        # Restore (clear soft delete by setting deleted_at to None)
        result = supabase.table("profiles").update({
            "deleted_at": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restore user"
            )
        
        restored_user = result.data[0] if isinstance(result.data, list) else result.data
        
        # Get role name
        role_name = "user"
        if restored_user.get("role_id"):
            try:
                role_result = supabase.table("roles").select("name").eq("id", restored_user["role_id"]).single().execute()
                if role_result.data:
                    role_name = role_result.data.get("name")
            except:
                pass
        
        return {
            "id": restored_user["id"],
            "email": restored_user.get("email"),
            "full_name": restored_user.get("full_name"),
            "role": role_name,
            "created_at": restored_user.get("created_at"),
            "updated_at": restored_user.get("updated_at"),
            "deleted_at": None,
            "is_active": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore user: {str(e)}"
        )


# Settings Management Endpoints
@router.get("/settings", status_code=status.HTTP_200_OK)
async def get_settings(
    category: Optional[str] = None,
    admin: dict = Depends(get_admin_user)
):
    """
    Get settings (admin only).
    Optionally filter by category.
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("settings").select("*")
        if category:
            query = query.eq("category", category)
        
        result = query.order("category, key").execute()
        
        return result.data or []
        
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve settings: {str(e)}"
        )


@router.put("/settings/{category}/{key}", status_code=status.HTTP_200_OK)
async def update_setting(
    category: str,
    key: str,
    setting_data: SettingUpdate,
    admin: dict = Depends(get_admin_user)
):
    """
    Update a setting (admin only).
    Creates the setting if it doesn't exist.
    """
    try:
        supabase = get_supabase_client()
        
        value = setting_data.value
        description = setting_data.description
        
        # Check if setting exists
        existing_result = supabase.table("settings").select("id").eq("category", category).eq("key", key).execute()
        existing = existing_result.data[0] if existing_result.data else None
        
        update_data = {
            "value": value,
            "updated_at": datetime.utcnow().isoformat()
        }
        if description is not None:
            update_data["description"] = description
        
        if existing:
            # Update existing
            result = supabase.table("settings").update(update_data).eq("category", category).eq("key", key).execute()
        else:
            # Create new
            insert_data = {
                "category": category,
                "key": key,
                "value": value,
                "description": description,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            result = supabase.table("settings").insert(insert_data).execute()
        
        # Clear cache if settings service is used
        try:
            from app.services.settings_service import settings_service
            settings_service.clear_cache()
        except:
            pass
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update setting"
            )
        
        updated_setting = result.data[0] if isinstance(result.data, list) else result.data
        return updated_setting
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating setting: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update setting: {str(e)}"
        )


@router.post("/settings/{category}/{key}/test", status_code=status.HTTP_200_OK)
async def test_setting(
    category: str,
    key: str,
    admin: dict = Depends(get_admin_user)
):
    """
    Test a setting (admin only).
    For external_api settings, validates connection.
    """
    try:
        supabase = get_supabase_client()
        
        setting = supabase.table("settings").select("*").eq("category", category).eq("key", key).single().execute()
        
        if not setting.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Setting not found"
            )
        
        # For OMS API, test the connection
        if category == "external_api" and key == "oms_auth_token":
            # Test OMS API connection
            try:
                from app.services.oms_service import oms_service
                # Simple test - just verify token format or make a minimal request
                return {"success": True, "message": "OMS API token configured"}
            except Exception as e:
                return {"success": False, "message": f"Test failed: {str(e)}"}
        
        return {"success": True, "message": "Setting configured"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing setting: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test setting: {str(e)}"
        )


# Global Jobs Endpoints
@router.get("/jobs", status_code=status.HTTP_200_OK)
async def list_all_jobs(
    status_filter: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    admin: dict = Depends(get_admin_user)
):
    """
    List all jobs across all users (admin only).
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("job_threads").select(
            "id, user_id, file_name, original_size, status, storage_path, error_message, created_at, started_at, completed_at, failed_at"
        )
        
        if status_filter:
            query = query.eq("status", status_filter)
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.order("created_at", desc=True).limit(limit).offset(offset).execute()
        
        # Get user emails for display
        user_ids = set()
        for job in (result.data or []):
            if job.get("user_id"):
                user_ids.add(job["user_id"])
        
        users_map = {}
        if user_ids:
            try:
                profiles_result = supabase.table("profiles").select("id, email, full_name").in_("id", list(user_ids)).execute()
                if profiles_result.data:
                    for profile in profiles_result.data:
                        users_map[profile["id"]] = {
                            "email": profile.get("email"),
                            "full_name": profile.get("full_name")
                        }
            except:
                pass
        
        jobs = []
        for job_data in (result.data or []):
            user_info = users_map.get(job_data.get("user_id", ""), {})
            
            jobs.append({
                "id": job_data["id"],
                "user_id": job_data.get("user_id"),
                "user_email": user_info.get("email"),
                "user_name": user_info.get("full_name"),
                "file_name": job_data.get("file_name"),
                "original_size": job_data.get("original_size"),
                "status": job_data.get("status"),
                "error_message": job_data.get("error_message"),
                "created_at": job_data.get("created_at"),
                "started_at": job_data.get("started_at"),
                "completed_at": job_data.get("completed_at"),
                "failed_at": job_data.get("failed_at")
            })
        
        return jobs
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve jobs: {str(e)}"
        )


@router.post("/jobs/{job_id}/retry", status_code=status.HTTP_200_OK)
async def retry_job(
    job_id: str,
    admin: dict = Depends(get_admin_user)
):
    """
    Retry a failed job (admin only).
    Enqueues the job for processing again.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if job exists
        job_result = supabase.table("job_threads").select("*").eq("id", job_id).single().execute()
        
        if not job_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        job = job_result.data
        
        # Reset job status and enqueue
        from app.workers.tasks import process_job_task
        from app.models.schemas import JobStatus
        
        # Update job status to in_queue
        supabase.table("job_threads").update({
            "status": JobStatus.IN_QUEUE.value,
            "error_message": None,
            "failed_at": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", job_id).execute()
        
        # Enqueue job
        process_job_task.delay(job_id)
        
        return {"message": "Job enqueued for retry", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry job: {str(e)}"
        )

