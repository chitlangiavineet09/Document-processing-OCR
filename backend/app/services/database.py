from supabase import create_client, Client
from app.core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Singleton pattern for Supabase client
_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client instance (using anon key)"""
    global _supabase_client
    
    if _supabase_client is None:
        try:
            _supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    return _supabase_client


def get_supabase_admin_client() -> Client:
    """Get or create Supabase admin client instance (using service role key, bypasses RLS)"""
    global _supabase_admin_client
    
    if _supabase_admin_client is None:
        if not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required for admin operations")
        try:
            _supabase_admin_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
            logger.info("Supabase admin client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase admin client: {str(e)}")
            raise
    
    return _supabase_admin_client

