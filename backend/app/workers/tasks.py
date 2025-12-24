from app.workers.celery_app import celery_app
from app.services.database import get_supabase_client
from app.services.storage import storage_service
from app.services.document_service import document_service
from app.services.openai_service import openai_service
from app.services.po_extraction_service import po_extraction_service
from app.services.items_extraction_service import items_extraction_service
from app.models.schemas import JobStatus, DocType, DocStatus
from datetime import datetime
import logging
import uuid
import os

logger = logging.getLogger(__name__)

# Ensure logger is configured with INFO level
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


@celery_app.task(bind=True, name="process_job", max_retries=3)
def process_job_task(self, job_id: str):
    """
    Process a job: OCR and classification.
    
    Full Phase 2 implementation:
    1. Fetch job details and file from storage
    2. Split document into pages
    3. Classify each page (bill/eway_bill/unknown)
    4. Run OCR on each classified page
    5. Save Doc records for each page
    6. Update job status
    
    Args:
        job_id: ID of the job thread to process
    """
    # #region agent log
    task_id = self.request.id if hasattr(self.request, 'id') else None
    logger.info(f"[DEBUG-HYP-D] Task received by worker - job_id: {job_id}, task_id: {task_id}")
    # #endregion
    # Use both logger and print to ensure visibility
    message = f"[{job_id}] Starting job processing"
    logger.info(message)
    print(message)  # Also print to ensure it's visible
    
    supabase = get_supabase_client()
    
    try:
        # Fetch job details
        job_result = supabase.table("job_threads").select("*").eq("id", job_id).execute()
        
        if not job_result.data:
            raise Exception(f"Job {job_id} not found")
        
        job = job_result.data[0]
        storage_path = job.get("storage_path")
        file_name = job.get("file_name", "document.pdf")
        user_id = job.get("user_id")
        
        if not storage_path:
            raise Exception(f"No storage_path found for job {job_id}")
        
        message = f"[{job_id}] Processing file: {file_name} from {storage_path}"
        logger.info(message)
        print(message)
        
        # Update job status to processing
        supabase.table("job_threads").update({
            "status": JobStatus.PROCESSING.value,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", job_id).execute()
        
        # Download file from storage
        message = f"[{job_id}] Downloading file from storage..."
        logger.info(message)
        print(message)
        file_bytes = storage_service.download_file(storage_path)
        message = f"[{job_id}] Downloaded {len(file_bytes)} bytes"
        logger.info(message)
        print(message)
        
        # Get file extension
        file_ext = os.path.splitext(file_name)[1].lower()
        if not file_ext:
            file_ext = ".pdf"  # Default to PDF if no extension
        
        # Split document into pages
        message = f"[{job_id}] Splitting document into pages..."
        logger.info(message)
        print(message)
        pages = document_service.get_image_bytes_for_classification(file_bytes, file_ext)
        message = f"[{job_id}] Split into {len(pages)} pages"
        logger.info(message)
        print(message)
        
        # Process each page
        doc_records = []
        classification_errors = []
        
        for page_number, page_bytes in pages:
            logger.info(f"[{job_id}] Processing page {page_number}/{len(pages)}")
            
            try:
                # Classify the page
                classification = openai_service.classify_document(page_bytes, file_name)
                logger.info(f"[{job_id}] Page {page_number} classified as: {classification}")
                print(f"[{job_id}] Page {page_number} classified as: {classification}")
                
                # Determine doc_type and status
                if classification == 'bill':
                    doc_type = DocType.BILL
                    doc_status = DocStatus.DRAFT_PENDING
                elif classification == 'eway_bill':
                    doc_type = DocType.EWAY_BILL
                    doc_status = DocStatus.DRAFT_PENDING
                else:
                    doc_type = DocType.UNKNOWN
                    doc_status = DocStatus.UNKNOWN
                
                # Run OCR if not unknown
                ocr_payload = None
                extracted_po_number = None
                if doc_type != DocType.UNKNOWN:
                    logger.info(f"[{job_id}] Running OCR on page {page_number}...")
                    print(f"[{job_id}] Running OCR on page {page_number}...")
                    ocr_payload = openai_service.extract_ocr_data(page_bytes, classification, file_name)
                    logger.info(f"[{job_id}] OCR completed for page {page_number}")
                    print(f"[{job_id}] OCR completed for page {page_number}")
                    
                    # Extract PO number and items from OCR payload
                    extracted_items = None
                    extracted_po_number = None
                    if ocr_payload:
                        try:
                            extracted_po_number = po_extraction_service.extract_po_number(ocr_payload)
                            if extracted_po_number:
                                logger.info(f"[{job_id}] Extracted PO number: {extracted_po_number}")
                                print(f"[{job_id}] Extracted PO number: {extracted_po_number}")
                            else:
                                logger.info(f"[{job_id}] No PO number found in OCR payload")
                                print(f"[{job_id}] No PO number found in OCR payload")
                        except Exception as po_extract_error:
                            logger.warning(f"[{job_id}] Failed to extract PO number: {str(po_extract_error)}")
                            print(f"[{job_id}] Failed to extract PO number: {str(po_extract_error)}")
                        
                        # Extract items from OCR payload
                        try:
                            extracted_items = items_extraction_service.extract_items(ocr_payload)
                            if extracted_items:
                                logger.info(f"[{job_id}] Extracted {len(extracted_items)} items from OCR payload")
                                print(f"[{job_id}] Extracted {len(extracted_items)} items from OCR payload")
                            else:
                                logger.info(f"[{job_id}] No items found in OCR payload")
                                print(f"[{job_id}] No items found in OCR payload")
                        except Exception as items_extract_error:
                            logger.warning(f"[{job_id}] Failed to extract items: {str(items_extract_error)}")
                            print(f"[{job_id}] Failed to extract items: {str(items_extract_error)}")
                
                # Upload page image to storage
                page_storage_path = storage_service.upload_page(
                    page_bytes=page_bytes,
                    job_id=job_id,
                    page_number=page_number,
                    file_extension="png"
                )
                logger.info(f"[{job_id}] Page {page_number} uploaded to: {page_storage_path}")
                print(f"[{job_id}] Page {page_number} uploaded to: {page_storage_path}")
                
                # Create Doc record
                doc_id = str(uuid.uuid4())
                doc_data = {
                    "id": doc_id,
                    "job_thread_id": job_id,
                    "user_id": user_id,
                    "page_number": page_number,
                    "doc_type": doc_type.value,
                    "status": doc_status.value,
                    "ocr_payload": ocr_payload,
                    "po_number": extracted_po_number,  # Extracted PO number
                    "items": extracted_items,  # Extracted and formatted items
                    "storage_uri": page_storage_path,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                result = supabase.table("docs").insert(doc_data).execute()
                
                if result.data:
                    doc_records.append(doc_id)
                    logger.info(f"[{job_id}] Created Doc record {doc_id} for page {page_number}")
                else:
                    logger.error(f"[{job_id}] Failed to create Doc record for page {page_number}")
                
            except Exception as page_error:
                error_msg = str(page_error)
                logger.error(f"[{job_id}] Error processing page {page_number}: {error_msg}", exc_info=True)
                print(f"[{job_id}] Error processing page {page_number}: {error_msg}")
                
                # Store classification errors for reporting
                if "classification" in error_msg.lower() or "prompt" in error_msg.lower():
                    classification_errors.append(f"Page {page_number}: {error_msg}")
                
                # Create a Doc record with error status for failed pages
                try:
                    doc_id = str(uuid.uuid4())
                    doc_data = {
                        "id": doc_id,
                        "job_thread_id": job_id,
                        "user_id": user_id,
                        "page_number": page_number,
                        "doc_type": DocType.UNKNOWN.value,
                        "status": DocStatus.UNKNOWN.value,
                        "ocr_payload": {"error": error_msg},
                        "storage_uri": None,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    result = supabase.table("docs").insert(doc_data).execute()
                    if result.data:
                        logger.info(f"[{job_id}] Created error Doc record {doc_id} for page {page_number}")
                except Exception as doc_error:
                    logger.error(f"[{job_id}] Failed to create error doc record: {str(doc_error)}")
                
                # Continue processing other pages
                continue
        
        # Update job status to processed
        message = f"[{job_id}] Processing complete. Created {len(doc_records)} Doc records"
        logger.info(message)
        print(message)
        
        # If there were classification errors, add them to error_message
        error_message = None
        if classification_errors:
            error_message = f"Classification errors on some pages: {'; '.join(classification_errors)}"
            logger.warning(f"[{job_id}] {error_message}")
            print(f"[{job_id}] {error_message}")
        
        update_data = {
            "status": JobStatus.PROCESSED.value,
            "completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if error_message:
            update_data["error_message"] = error_message
        
        supabase.table("job_threads").update(update_data).eq("id", job_id).execute()
        
        message = f"[{job_id}] Job completed successfully"
        logger.info(message)
        print(message)
        
    except Exception as e:
        logger.error(f"[{job_id}] Job processing failed: {str(e)}", exc_info=True)
        
        # Update job status to error
        try:
            supabase.table("job_threads").update({
                "status": JobStatus.ERROR.value,
                "error_message": str(e),
                "failed_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", job_id).execute()
        except Exception as update_error:
            logger.error(f"[{job_id}] Failed to update error status: {str(update_error)}")
        
        # Re-raise to trigger Celery retry if configured
        raise

