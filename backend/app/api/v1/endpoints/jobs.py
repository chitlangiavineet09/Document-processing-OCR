from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional, List
from datetime import datetime
import logging
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.security import generate_request_id
from app.models.schemas import (
    JobThreadCreate,
    JobThreadOut,
    JobThreadSummary,
    FileUploadResponse,
    JobUpdateResponse,
    JobStatus,
    DocOut,
    DocType,
    DocStatus,
    ErrorResponse
)
from app.services.database import get_supabase_client
from app.services.storage import storage_service
from app.workers.tasks import process_job_task
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


def validate_file(file: UploadFile) -> tuple:
    """
    Validate uploaded file.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check file extension
    if not file.filename:
        return False, "Filename is required"
    
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        return False, f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
    
    return True, ""


@router.post("/", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    file: UploadFile = File(..., description="File to upload (PDF, PNG, JPG, JPEG)"),
    user: dict = Depends(get_current_user)
):
    """
    Upload a file and create a new job thread for OCR/classification.
    
    Validates file type and size, uploads to storage, creates job record,
    and enqueues processing task.
    """
    request_id = generate_request_id()
    user_id = user["user_id"]
    
    logger.info(f"[{request_id}] File upload request from user {user_id}: {file.filename}")
    
    try:
        # Validate file extension
        is_valid, error_msg = validate_file(file)
        if not is_valid:
            logger.warning(f"[{request_id}] Validation failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        if file_size > settings.MAX_UPLOAD_SIZE:
            logger.warning(f"[{request_id}] File too large: {file_size} bytes")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE / (1024*1024)} MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Upload file to Supabase Storage
        try:
            storage_path = storage_service.upload_file(
                file_content=file_content,
                file_name=file.filename,
                job_id=job_id,
                folder="jobs"
            )
            logger.info(f"[{request_id}] File uploaded to storage: {storage_path}")
        except Exception as e:
            logger.error(f"[{request_id}] Storage upload failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to storage: {str(e)}"
            )
        
        # Create job thread record in database
        supabase = get_supabase_client()
        try:
            job_data = {
                "id": job_id,
                "user_id": user_id,
                "file_name": file.filename,
                "original_size": file_size,
                "status": JobStatus.IN_QUEUE.value,
                "storage_path": storage_path,
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"[{request_id}] Inserting job data: {job_data}")
            result = supabase.table("job_threads").insert(job_data).execute()
            
            if not result.data:
                logger.error(f"[{request_id}] Insert result: {result}")
                raise Exception("Failed to insert job thread: No data returned")
            
            logger.info(f"[{request_id}] Job thread created: {job_id}")
        except Exception as e:
            logger.error(f"[{request_id}] Database insert failed: {str(e)}", exc_info=True)
            # Try to clean up uploaded file
            try:
                storage_service.delete_file(storage_path)
            except Exception as cleanup_error:
                logger.error(f"[{request_id}] Cleanup failed: {str(cleanup_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create job record: {str(e)}"
            )
        
        # Enqueue Celery task for processing
        try:
            process_job_task.delay(job_id)
            logger.info(f"[{request_id}] Job task enqueued: {job_id}")
        except Exception as e:
            logger.error(f"[{request_id}] Failed to enqueue task: {str(e)}", exc_info=True)
            # Job is created, but task might fail - status will remain IN_QUEUE
            # Could add retry logic or manual trigger endpoint
            # Don't fail the request if enqueueing fails - job is already created
        
        return FileUploadResponse(
            job_id=job_id,
            status=JobStatus.IN_QUEUE,
            message="File uploaded successfully. Processing started.",
            file_name=file.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/", response_model=List[JobThreadSummary])
async def list_jobs(
    status_filter: Optional[JobStatus] = None,
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user)
):
    """
    Get list of jobs for the authenticated user.
    Supports filtering by status and pagination.
    """
    user_id = user["user_id"]
    
    try:
        supabase = get_supabase_client()
        query = supabase.table("job_threads").select("*").eq("user_id", user_id)
        
        if status_filter:
            query = query.eq("status", status_filter.value)
        
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        
        jobs = []
        for job_data in result.data:
            # Get document count for this job
            doc_result = supabase.table("docs").select("id", count="exact").eq("job_thread_id", job_data["id"]).execute()
            # Supabase returns count in different formats - handle both
            if hasattr(doc_result, 'count'):
                doc_count = doc_result.count
            elif isinstance(doc_result, dict) and 'count' in doc_result:
                doc_count = doc_result['count']
            else:
                # Fallback: count the data length
                doc_count = len(doc_result.data) if doc_result.data else 0
            
            # Check if documents can be reviewed
            can_review = (
                job_data["status"] == JobStatus.PROCESSED.value and
                doc_count > 0
            )
            
            # Parse dates safely
            try:
                created_at_str = job_data["created_at"]
                if isinstance(created_at_str, str):
                    if created_at_str.endswith("Z"):
                        created_at_str = created_at_str.replace("Z", "+00:00")
                    created_at = datetime.fromisoformat(created_at_str)
                else:
                    created_at = datetime.utcnow()
            except Exception as date_error:
                logger.warning(f"Failed to parse created_at for job {job_data['id']}: {date_error}, using current time")
                created_at = datetime.utcnow()
            
            completed_at = None
            if job_data.get("completed_at"):
                try:
                    completed_at_str = job_data["completed_at"]
                    if isinstance(completed_at_str, str):
                        if completed_at_str.endswith("Z"):
                            completed_at_str = completed_at_str.replace("Z", "+00:00")
                        completed_at = datetime.fromisoformat(completed_at_str)
                except Exception as date_error:
                    logger.warning(f"Failed to parse completed_at for job {job_data['id']}: {date_error}")
                    completed_at = None
            
            jobs.append(JobThreadSummary(
                id=job_data["id"],
                file_name=job_data["file_name"],
                status=JobStatus(job_data["status"]),
                created_at=created_at,
                completed_at=completed_at,
                error_message=job_data.get("error_message"),
                document_count=doc_count,
                can_review_docs=can_review
            ))
        
        return jobs
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve jobs: {str(e)}"
        )


@router.get("/updates", response_model=List[JobUpdateResponse])
async def get_job_updates(
    since: Optional[datetime] = None,
    user: dict = Depends(get_current_user)
):
    """
    Get job updates since a given timestamp.
    Used for polling job status changes.
    """
    user_id = user["user_id"]
    
    try:
        supabase = get_supabase_client()
        query = supabase.table("job_threads").select("*").eq("user_id", user_id)
        
        if since:
            query = query.gte("updated_at", since.isoformat())
        
        query = query.order("updated_at", desc=True).limit(50)
        result = query.execute()
        
        updates = []
        for job_data in result.data:
            updates.append(JobUpdateResponse(
                id=job_data["id"],
                file_name=job_data["file_name"],
                status=JobStatus(job_data["status"]),
                updated_at=datetime.fromisoformat(job_data["updated_at"].replace("Z", "+00:00")),
                error_message=job_data.get("error_message")
            ))
        
        return updates
        
    except Exception as e:
        logger.error(f"Failed to get job updates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job updates"
        )


@router.get("/{job_id}", response_model=JobThreadOut)
async def get_job(
    job_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get details of a specific job.
    """
    user_id = user["user_id"]
    
    try:
        supabase = get_supabase_client()
        result = supabase.table("job_threads").select("*").eq("id", job_id).eq("user_id", user_id).single().execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        job_data = result.data
        return JobThreadOut(
            id=job_data["id"],
            user_id=job_data["user_id"],
            file_name=job_data["file_name"],
            original_size=job_data["original_size"],
            status=JobStatus(job_data["status"]),
            storage_path=job_data.get("storage_path"),
            error_message=job_data.get("error_message"),
            created_at=datetime.fromisoformat(job_data["created_at"].replace("Z", "+00:00")),
            started_at=datetime.fromisoformat(job_data["started_at"].replace("Z", "+00:00")) if job_data.get("started_at") else None,
            completed_at=datetime.fromisoformat(job_data["completed_at"].replace("Z", "+00:00")) if job_data.get("completed_at") else None,
            failed_at=datetime.fromisoformat(job_data["failed_at"].replace("Z", "+00:00")) if job_data.get("failed_at") else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job"
        )


@router.get("/{job_id}/documents", response_model=List[DocOut])
async def get_job_documents(
    job_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get all documents for a specific job, sorted by page number.
    Enforces ownership: user can only see documents from their own jobs.
    """
    user_id = user["user_id"]
    
    try:
        supabase = get_supabase_client()
        
        # First verify the job exists and belongs to the user
        job_result = supabase.table("job_threads").select("id, user_id, status").eq("id", job_id).single().execute()
        
        if not job_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        job = job_result.data
        if job["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: job belongs to another user"
            )
        
        # Get all documents for this job, sorted by page number
        docs_result = supabase.table("docs").select("*").eq("job_thread_id", job_id).order("page_number", desc=False).execute()
        
        documents = []
        for doc_data in docs_result.data:
            # Parse dates safely
            try:
                created_at_str = doc_data["created_at"]
                if isinstance(created_at_str, str):
                    if created_at_str.endswith("Z"):
                        created_at_str = created_at_str.replace("Z", "+00:00")
                    created_at = datetime.fromisoformat(created_at_str)
                else:
                    created_at = datetime.utcnow()
            except Exception as date_error:
                logger.warning(f"Failed to parse created_at for doc {doc_data['id']}: {date_error}")
                created_at = datetime.utcnow()
            
            try:
                updated_at_str = doc_data["updated_at"]
                if isinstance(updated_at_str, str):
                    if updated_at_str.endswith("Z"):
                        updated_at_str = updated_at_str.replace("Z", "+00:00")
                    updated_at = datetime.fromisoformat(updated_at_str)
                else:
                    updated_at = datetime.utcnow()
            except Exception as date_error:
                logger.warning(f"Failed to parse updated_at for doc {doc_data['id']}: {date_error}")
                updated_at = datetime.utcnow()
            
            documents.append(DocOut(
                id=doc_data["id"],
                job_thread_id=doc_data["job_thread_id"],
                user_id=doc_data["user_id"],
                page_number=doc_data["page_number"],
                doc_type=DocType(doc_data["doc_type"]),
                status=DocStatus(doc_data["status"]),
                ocr_payload=doc_data.get("ocr_payload"),
                po_number=doc_data.get("po_number"),
                items=doc_data.get("items"),
                storage_uri=doc_data.get("storage_uri"),
                created_at=created_at,
                updated_at=updated_at
            ))
        
        return documents
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )

