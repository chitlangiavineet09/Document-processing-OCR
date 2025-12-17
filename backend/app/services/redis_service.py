"""Service for Redis operations (draft session state)"""
from typing import Optional, Dict, Any
import json
import redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Redis client singleton
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client"""
    global _redis_client
    
    if _redis_client is None:
        try:
            redis_url = settings.REDIS_URL
            
            # For Upstash (rediss://), we need to handle SSL properly
            if redis_url.startswith('rediss://'):
                # Parse URL and create client with SSL configuration
                from urllib.parse import urlparse
                parsed = urlparse(redis_url)
                
                _redis_client = redis.Redis(
                    host=parsed.hostname,
                    port=parsed.port or 6380,
                    password=parsed.password,
                    ssl=True,
                    ssl_cert_reqs=None,  # Disable SSL certificate verification for Upstash
                    decode_responses=True
                )
            else:
                # Standard redis:// URL (local or non-SSL)
                _redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            _redis_client.ping()
            logger.info("Redis client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {str(e)}")
            raise
    
    return _redis_client


class RedisService:
    """Service for managing draft session state in Redis"""

    def __init__(self):
        # Lazy initialization - don't fail on module import
        self._client = None
        self.session_ttl = 3600  # 1 hour TTL for draft sessions
    
    @property
    def client(self):
        """Lazy-load Redis client on first use"""
        if self._client is None:
            self._client = get_redis_client()
        return self._client

    def set_draft_session(self, session_key: str, data: Dict[str, Any]) -> bool:
        """
        Store draft session data in Redis.
        
        Args:
            session_key: Unique session key (e.g., f"draft_session:{doc_id}")
            data: Dictionary containing session data
            
        Returns:
            True if successful
        """
        try:
            json_data = json.dumps(data)
            self.client.setex(session_key, self.session_ttl, json_data)
            logger.info(f"Stored draft session: {session_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to store draft session: {str(e)}")
            raise

    def get_draft_session(self, session_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve draft session data from Redis.
        
        Args:
            session_key: Unique session key
            
        Returns:
            Dictionary containing session data, or None if not found
        """
        try:
            json_data = self.client.get(session_key)
            if json_data:
                return json.loads(json_data)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve draft session: {str(e)}")
            return None

    def delete_draft_session(self, session_key: str) -> bool:
        """
        Delete draft session data from Redis.
        
        Args:
            session_key: Unique session key
            
        Returns:
            True if successful
        """
        try:
            self.client.delete(session_key)
            logger.info(f"Deleted draft session: {session_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete draft session: {str(e)}")
            return False

    def extend_session_ttl(self, session_key: str) -> bool:
        """Extend session TTL"""
        try:
            return self.client.expire(session_key, self.session_ttl)
        except Exception as e:
            logger.error(f"Failed to extend session TTL: {str(e)}")
            return False


# Singleton instance - lazy initialization to avoid startup errors
redis_service = RedisService()

