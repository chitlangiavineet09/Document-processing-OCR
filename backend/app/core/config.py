from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str  # Anon key for client-side operations
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None  # Service role key for admin operations (bypasses RLS)
    SUPABASE_JWT_SECRET: str
    SUPABASE_STORAGE_BUCKET: str = "bill-uploads"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    
    # Redis & Celery Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # OMS API Configuration (can be configured via settings table later)
    OMS_API_BASE_URL: str = "https://api.zetwerk.com/oms/v1"
    OMS_AUTH_TOKEN: Optional[str] = None
    
    # CORS Configuration
    # Store as string (comma-separated) to avoid JSON parsing issues
    # Will be converted to list by validator
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, list, None]) -> str:
        """
        Convert CORS origins to comma-separated string.
        We'll parse this in main.py to get the list.
        """
        if v is None:
            return "http://localhost:3000,http://127.0.0.1:3000"
        
        if isinstance(v, list):
            # Convert list to comma-separated string
            return ",".join([str(item).rstrip('/') for item in v if item])
        
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                return "http://localhost:3000,http://127.0.0.1:3000"
            
            # If it's a JSON array string, parse it
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return ",".join([str(item).rstrip('/') for item in parsed if item])
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # Already comma-separated string, just return it (trimmed)
            return ",".join([i.strip().rstrip('/') for i in v.split(",") if i.strip()])
        
        # Fallback to default
        return "http://localhost:3000,http://127.0.0.1:3000"
    
    # File Upload Configuration
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5 MB in bytes
    ALLOWED_EXTENSIONS: List[str] = [".png", ".jpg", ".jpeg", ".pdf"]
    
    # Application Settings
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Server Configuration (for Render.com and other platforms)
    PORT: int = 8000  # Default port, Render will set PORT env variable
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()

