"""Service for OpenAI API interactions (classification and OCR)"""
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.settings_service import settings_service
import logging
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI API interactions"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def classify_document(self, image_bytes: bytes, file_name: str = "document.png") -> str:
        """
        Classify a document page as 'bill', 'eway_bill', or 'unknown'.
        
        Args:
            image_bytes: Image bytes (PNG/JPEG) or first page of PDF as image
            file_name: Original file name (for context)
        
        Returns:
            Classification result: 'bill', 'eway_bill', or 'unknown'
        """
        try:
            # Get prompt and model from settings
            default_prompt = """You are a document classifier. Analyze the provided image and classify it into one of these categories:
- 'bill': If it's an invoice or bill document
- 'eway_bill': If it's an e-way bill document
- 'unknown': If it doesn't match either category

Respond with ONLY one word: 'bill', 'eway_bill', or 'unknown'. Do not include any explanation or additional text."""
            
            try:
                prompt = settings_service.get_llm_prompt(
                    "classification_prompt",
                    default=default_prompt
                )
            except ValueError as e:
                logger.error(f"Failed to get classification prompt: {str(e)}")
                raise Exception(f"Classification prompt not configured: {str(e)}. Please configure it in Settings.")
            
            # Validate prompt is not empty
            if not prompt or not prompt.strip():
                error_msg = "Classification prompt is empty. Please configure it in Settings."
                logger.error(error_msg)
                raise Exception(error_msg)
            
            model = settings_service.get_llm_model("classification_model", default="gpt-4o")
            
            # Log prompt details for debugging
            logger.info("=" * 80)
            logger.info("CLASSIFICATION LLM REQUEST:")
            logger.info("=" * 80)
            logger.info(f"Using model: {model}")
            logger.info(f"Prompt (length: {len(prompt)} characters):")
            logger.info("-" * 80)
            logger.info(prompt)
            logger.info("-" * 80)
            logger.info("=" * 80)
            
            # Convert image bytes to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            mime_type = "image/png" if file_name.endswith('.png') else "image/jpeg"
            
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=10,
                temperature=0
            )
            
            classification_raw = response.choices[0].message.content.strip()
            classification = classification_raw.lower()
            
            logger.info("=" * 80)
            logger.info("CLASSIFICATION LLM RESPONSE:")
            logger.info("=" * 80)
            logger.info(f"Raw response: '{classification_raw}'")
            logger.info(f"Model: {model}")
            logger.info(f"Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 'N/A'}")
            logger.info("=" * 80)
            
            # Normalize response
            if 'bill' in classification and 'eway' not in classification:
                result = 'bill'
            elif 'eway' in classification:
                result = 'eway_bill'
            else:
                result = 'unknown'
            
            logger.info(f"Classification normalized to: '{result}'")
            return result
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Classification failed: {error_msg}", exc_info=True)
            print(f"Classification failed: {error_msg}")
            # Re-raise exception so it can be caught and stored in job/doc
            raise Exception(f"Document classification failed: {error_msg}")
    
    def extract_ocr_data(self, image_bytes: bytes, doc_type: str, file_name: str = "document.png") -> Dict[str, Any]:
        """
        Extract structured data from document using OCR.
        
        Args:
            image_bytes: Image bytes (PNG/JPEG)
            doc_type: Document type ('bill' or 'eway_bill')
            file_name: Original file name
        
        Returns:
            Dictionary with extracted OCR data
        """
        try:
            # Get prompt and model from settings
            # First try doc-type-specific key, then fallback to generic ocr_prompt
            default_ocr_prompt = f"""You are an OCR system. Extract all relevant data from this {doc_type} document.
Return the data as a JSON object. Include all fields like dates, invoice numbers, parties, items, amounts, taxes, etc.
Be thorough and extract all visible information. Return only valid JSON, no other text."""
            
            prompt = None
            prompt_key = None
            prompt_source_detail = ""
            
            # Try doc-type-specific key first (e.g., bill_ocr_prompt, eway_bill_ocr_prompt)
            if doc_type in ['bill', 'eway_bill']:
                specific_key = f"{doc_type}_ocr_prompt"
                try:
                    prompt = settings_service.get_llm_prompt(
                        specific_key,
                        default=None  # Don't use default yet, try generic key first
                    )
                    prompt_key = specific_key
                    prompt_source_detail = f"doc-type-specific key '{specific_key}'"
                    logger.info(f"Found OCR prompt using {prompt_source_detail}")
                except (ValueError, KeyError):
                    # Specific key doesn't exist or is empty, will try generic key
                    pass
            
            # Fallback to generic ocr_prompt if specific key not found or empty
            if not prompt:
                try:
                    prompt = settings_service.get_llm_prompt(
                        "ocr_prompt",
                        default=default_ocr_prompt
                    )
                    prompt_key = "ocr_prompt"
                    if prompt == default_ocr_prompt:
                        prompt_source_detail = "generic 'ocr_prompt' (empty, using DEFAULT)"
                    else:
                        prompt_source_detail = "generic 'ocr_prompt' (CUSTOM from database)"
                    logger.info(f"Using OCR prompt from {prompt_source_detail}")
                except ValueError as e:
                    logger.error(f"Failed to get OCR prompt: {str(e)}")
                    raise Exception(f"OCR prompt not configured: {str(e)}. Please configure it in Settings.")
            
            # Validate prompt is not empty
            if not prompt or not prompt.strip():
                error_msg = f"OCR prompt ({prompt_key}) is empty. Please configure it in Settings."
                logger.error(error_msg)
                raise Exception(error_msg)
            
            model = settings_service.get_llm_model("ocr_model", default="gpt-4o")
            
            # Determine if using default or custom prompt by checking if prompt matches default
            # Note: This is a best-effort check. If user saved the exact default text, it will show as custom.
            is_likely_default = prompt.strip() == default_ocr_prompt.strip()
            if is_likely_default:
                prompt_source = f"DEFAULT (fallback - {prompt_key} was empty in database)"
            else:
                prompt_source = f"CUSTOM (from database settings - {prompt_source_detail})"
            
            # Log prompt details for debugging
            logger.info("=" * 80)
            logger.info("OCR LLM REQUEST:")
            logger.info("=" * 80)
            logger.info(f"Prompt key used: {prompt_key}")
            logger.info(f"Prompt source: {prompt_source}")
            logger.info(f"Using model: {model}")
            logger.info(f"Document type: {doc_type}")
            logger.info(f"File name: {file_name}")
            logger.info(f"Prompt (length: {len(prompt)} characters):")
            logger.info("-" * 80)
            logger.info(prompt)
            logger.info("-" * 80)
            logger.info("=" * 80)
            
            # Convert image bytes to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            mime_type = "image/png" if file_name.endswith('.png') else "image/jpeg"
            
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=4000,
                temperature=0
            )
            
            # Parse JSON response
            import json
            result_text = response.choices[0].message.content.strip()
            
            # Log response details
            logger.info("=" * 80)
            logger.info("OCR LLM RESPONSE:")
            logger.info("=" * 80)
            logger.info(f"Raw response length: {len(result_text)} characters")
            logger.info(f"Model: {model}")
            logger.info(f"Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 'N/A'}")
            logger.info("Response preview (first 500 chars):")
            logger.info("-" * 80)
            logger.info(result_text[:500] + ("..." if len(result_text) > 500 else ""))
            logger.info("-" * 80)
            logger.info("=" * 80)
            
            ocr_data = json.loads(result_text)
            return ocr_data
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}", exc_info=True)
            return {"error": str(e), "raw_text": ""}


# Singleton instance
openai_service = OpenAIService()

