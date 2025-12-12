"""Service for fetching configuration from settings table"""
from typing import Optional, Dict, Any
from app.services.database import get_supabase_client
import logging

logger = logging.getLogger(__name__)

# Cache for settings (to avoid repeated DB queries)
_settings_cache: Optional[Dict[str, Any]] = None


class SettingsService:
    """Service for fetching and caching settings from database"""
    
    def __init__(self):
        self.client = get_supabase_client()
        self._cache = {}
    
    def _fetch_settings(self, category: str) -> Dict[str, str]:
        """Fetch settings for a category from database"""
        try:
            result = self.client.table("settings").select("*").eq("category", category).execute()
            
            settings = {}
            if result.data:
                for row in result.data:
                    settings[row["key"]] = row["value"]
            
            return settings
        except Exception as e:
            logger.error(f"Failed to fetch settings for category {category}: {str(e)}")
            return {}
    
    def get_llm_prompt(self, prompt_type: str, default: Optional[str] = None) -> str:
        """
        Get LLM prompt from settings table.
        
        Args:
            prompt_type: Type of prompt (classification_prompt, ocr_prompt, fuzzy_match_prompt)
            default: Default prompt if not found in database (None means raise error if not found)
        
        Returns:
            Prompt string
        
        Raises:
            ValueError: If prompt is not found and no default is provided
        """
        cache_key = f"llm_prompts_{prompt_type}"
        
        if cache_key not in self._cache:
            logger.debug(f"Prompt '{prompt_type}' not in cache, fetching from database...")
            settings = self._fetch_settings("llm")
            prompt_value = settings.get(prompt_type, None)
            
            logger.debug(f"Database value for '{prompt_type}': {'empty/None' if not prompt_value or not prompt_value.strip() else f'found ({len(prompt_value.strip())} chars)'}")
            
            # Check if value is empty/None and use default if so
            if not prompt_value or (isinstance(prompt_value, str) and not prompt_value.strip()):
                if default is not None:
                    logger.warning(f"Prompt '{prompt_type}' is empty in database, using DEFAULT prompt")
                    self._cache[cache_key] = default
                else:
                    error_msg = f"Prompt '{prompt_type}' is empty in database and no default provided"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            else:
                logger.info(f"Prompt '{prompt_type}' loaded from database (CUSTOM prompt, length: {len(prompt_value.strip())} chars)")
                # Show first 100 chars as preview
                preview = prompt_value.strip()[:100] + ("..." if len(prompt_value.strip()) > 100 else "")
                logger.debug(f"Prompt preview: {preview}")
                self._cache[cache_key] = prompt_value.strip()
        else:
            logger.debug(f"Prompt '{prompt_type}' found in cache (length: {len(self._cache[cache_key])} chars)")
        
        return self._cache[cache_key]
    
    def get_llm_model(self, model_type: str, default: str = "gpt-4o") -> str:
        """
        Get LLM model name from settings table.
        
        Args:
            model_type: Type of model (classification_model, ocr_model, fuzzy_match_model)
            default: Default model if not found
        
        Returns:
            Model name string
        """
        cache_key = f"llm_models_{model_type}"
        
        if cache_key not in self._cache:
            settings = self._fetch_settings("llm")
            self._cache[cache_key] = settings.get(model_type, default)
        
        return self._cache[cache_key]
    
    def clear_cache(self):
        """Clear settings cache (useful after settings update)"""
        self._cache.clear()
        logger.info("Settings cache cleared")


# Singleton instance
settings_service = SettingsService()

