from typing import Optional
from supabase import create_client, Client
from app.core.config import settings
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Storage client with service role key (bypasses RLS)
_storage_client: Optional[Client] = None

def get_storage_client() -> Client:
    """Get or create Supabase client for storage operations (uses service role key to bypass RLS)"""
    global _storage_client
    
    if _storage_client is None:
        try:
            # Use service role key if available, otherwise fall back to regular key
            # Service role key bypasses RLS policies
            storage_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
            _storage_client = create_client(
                settings.SUPABASE_URL,
                storage_key
            )
            logger.info("Storage client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize storage client: {str(e)}")
            raise
    
    return _storage_client


class StorageService:
    """Service for handling file uploads to Supabase Storage"""
    
    def __init__(self):
        # Use separate client with service role key for storage operations
        self.client = get_storage_client()
        self.bucket = settings.SUPABASE_STORAGE_BUCKET
    
    def _get_content_type(self, file_name: str) -> str:
        """Determine content type from file extension"""
        file_ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
        content_types = {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
        }
        return content_types.get(file_ext, 'application/octet-stream')
    
    def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        job_id: Optional[str] = None,
        folder: Optional[str] = None
    ) -> str:
        """
        Upload file to Supabase Storage.
        
        Args:
            file_content: File content as bytes
            file_name: Original file name
            job_id: Optional job ID for organizing files
            folder: Optional folder path
            
        Returns:
            Storage path/URI of uploaded file
        """
        try:
            # Generate unique file path
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            
            if folder:
                storage_path = f"{folder}/{job_id}_{timestamp}_{unique_id}_{file_name}"
            else:
                storage_path = f"jobs/{job_id or 'temp'}/{timestamp}_{unique_id}_{file_name}"
            
            # Determine content type from file extension
            content_type = self._get_content_type(file_name)
            logger.info(f"Uploading file {file_name} with content-type: {content_type}")
            
            # Upload to Supabase Storage
            response = self.client.storage.from_(self.bucket).upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": content_type}
            )
            
            if response:
                logger.info(f"File uploaded successfully: {storage_path}")
                return storage_path
            else:
                raise Exception("Upload response was empty")
                
        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            raise
    
    def get_file_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """
        Get signed URL for accessing file.
        
        Args:
            storage_path: Path to file in storage
            expires_in: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Signed URL for file access
        """
        try:
            response = self.client.storage.from_(self.bucket).create_signed_url(
                path=storage_path,
                expires_in=expires_in
            )
            return response.get("signedURL", "")
        except Exception as e:
            logger.error(f"Failed to get file URL: {str(e)}")
            raise
    
    def download_file(self, storage_path: str) -> bytes:
        """
        Download file from storage.
        
        Args:
            storage_path: Path to file in storage
        
        Returns:
            File content as bytes
        """
        try:
            response = self.client.storage.from_(self.bucket).download(storage_path)
            if response:
                return response
            else:
                raise Exception("Download response was empty")
        except Exception as e:
            logger.error(f"Failed to download file {storage_path}: {str(e)}")
            raise
    
    def upload_page(self, page_bytes: bytes, job_id: str, page_number: int, file_extension: str = "png") -> str:
        """
        Upload a page image to storage.
        
        Args:
            page_bytes: Page image bytes
            job_id: Job ID
            page_number: Page number (1-indexed)
            file_extension: File extension (default: png)
        
        Returns:
            Storage path/URI of uploaded page
        """
        file_name = f"page-{page_number}.{file_extension}"
        return self.upload_file(
            file_content=page_bytes,
            file_name=file_name,
            job_id=job_id,
            folder="jobs"
        )
    
    def delete_file(self, storage_path: str) -> bool:
        """Delete file from storage"""
        try:
            response = self.client.storage.from_(self.bucket).remove([storage_path])
            logger.info(f"File deleted: {storage_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}")
            return False


# Singleton instance
storage_service = StorageService()

