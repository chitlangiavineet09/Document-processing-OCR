"""Service for fuzzy matching bill items with order items using LLM"""
from typing import Dict, Any, List, Optional
import json
import logging
from app.services.openai_service import openai_service
from app.services.settings_service import settings_service

logger = logging.getLogger(__name__)


class FuzzyMatchService:
    """Service for fuzzy matching bill items with order items using LLM"""

    def match_items(
        self,
        bill_items: List[Dict[str, Any]],
        order_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Match bill items with order items using LLM fuzzy matching.
        
        Args:
            bill_items: List of bill items from OCR (each should have id, name, hsn, quantity, etc.)
            order_items: List of order items from OMS API (each should have name, masterItemName, hsnCode, etc.)
            
        Returns:
            Dictionary with 'matches' list and 'unmatched' list:
            {
                "matches": [{"billId": "b0", "poId": "p2"}, ...],
                "unmatched": ["b3", ...]
            }
        """
        try:
            # Prepare bill items for LLM (items come from docs.items column which already has formatted structure)
            bill_items_formatted = []
            for idx, item in enumerate(bill_items):
                bill_id = item.get("billId", f"b{idx}")  # Use existing billId if present
                
                # Format item for LLM matching
                formatted_item = {
                    "billId": bill_id,
                    "name": item.get("name", "") or "",
                    "hsn_sac": item.get("hsn_sac", "") or "",  # HSN/SAC code
                    "quantity": item.get("quantity"),
                    "amount": item.get("amount"),
                    "unit": item.get("unit"),
                    "rate": item.get("rate"),
                    "original_index": idx  # Keep original index for reference
                }
                
                bill_items_formatted.append(formatted_item)
            
            # Prepare order items for LLM (with IDs)
            order_items_formatted = []
            for idx, item in enumerate(order_items):
                po_id = f"p{idx}"
                order_items_formatted.append({
                    "poId": po_id,
                    "name": item.get("name", item.get("masterItemName", "")) or "",
                    "masterItemName": item.get("masterItemName", ""),
                    "hsn_sac": item.get("hsnCode", ""),  # HSN/SAC code
                    "original_index": idx  # Keep original index for reference
                })
            
            # Get fuzzy match prompt from settings
            default_prompt = """You are a fuzzy matcher with high confidence. Task: produce a ONE-TO-ONE mapping from bill items to PO items.

Rules:

1. Fuzzy Match based on item name semantics and HSN/SAC code

2. If HSN/SAC differs, you MAY still match based on strong name semantics, but only if there is high confidence and no better HSN/SAC alternative.

3. Each billId MUST map to EXACTLY ONE poId.

4. Each poId MUST be used AT MOST ONCE (no two bill items may map to the same PO item).

5. If any billId cannot be matched confidently, list it under unmatched and DO NOT guess.

Return STRICT JSON ONLY with this exact shape:

{
  "matches": [{"billId": "b0", "poId": "p2"}],
  "unmatched": ["b3"]
}"""

            try:
                prompt = settings_service.get_llm_prompt(
                    "fuzzy_match_prompt",
                    default=default_prompt
                )
            except ValueError as e:
                logger.warning(f"Failed to get fuzzy match prompt from settings, using default: {str(e)}")
                prompt = default_prompt

            # Build the matching prompt with actual data
            matching_prompt = f"""{prompt}

Bill Items:
{json.dumps(bill_items_formatted, indent=2)}

Order Items:
{json.dumps(order_items_formatted, indent=2)}

Return the JSON mapping now:"""

            logger.info(f"Matching {len(bill_items_formatted)} bill items with {len(order_items_formatted)} order items")
            
            # Log the full request being sent to LLM
            logger.info("=" * 80)
            logger.info("FUZZY MATCH LLM REQUEST:")
            logger.info("=" * 80)
            logger.info(f"Prompt: {prompt}")
            logger.info(f"Bill Items: {json.dumps(bill_items_formatted, indent=2)}")
            logger.info(f"Order Items: {json.dumps(order_items_formatted, indent=2)}")
            logger.info("=" * 80)
            
            # Call OpenAI for fuzzy matching
            # Use a text-based model for this task
            model = settings_service.get_llm_model("fuzzy_match_model", default="gpt-4o")
            logger.info(f"Using model: {model}")
            
            from openai import OpenAI
            from app.core.config import settings
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise matching system that returns only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": matching_prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0,  # Low temperature for consistent matching
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Log the full response from LLM
            logger.info("=" * 80)
            logger.info("FUZZY MATCH LLM RESPONSE:")
            logger.info("=" * 80)
            logger.info(f"Raw response: {result_text}")
            logger.info(f"Model: {model}")
            logger.info(f"Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 'N/A'}")
            logger.info("=" * 80)
            
            # Parse JSON response
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {result_text}")
                raise Exception(f"LLM returned invalid JSON: {str(e)}")
            
            # Validate response structure
            if "matches" not in result or "unmatched" not in result:
                raise Exception("LLM response missing required fields: 'matches' or 'unmatched'")
            
            # Convert billId/poId back to original indices
            matches_with_indices = []
            for match in result.get("matches", []):
                bill_id = match.get("billId", "")
                po_id = match.get("poId", "")
                
                # Find original indices
                bill_idx = self._find_index_by_id(bill_items_formatted, "billId", bill_id)
                po_idx = self._find_index_by_id(order_items_formatted, "poId", po_id)
                
                if bill_idx is not None and po_idx is not None:
                    matches_with_indices.append({
                        "billIndex": bill_idx,
                        "orderIndex": po_idx,
                        "billItem": bill_items[bill_idx],
                        "orderItem": order_items[po_idx]
                    })
                else:
                    logger.warning(f"Could not resolve indices for match: {match}")
            
            unmatched_indices = []
            for unmatched_id in result.get("unmatched", []):
                bill_idx = self._find_index_by_id(bill_items_formatted, "billId", unmatched_id)
                if bill_idx is not None:
                    unmatched_indices.append(bill_idx)
            
            logger.info(f"Matched {len(matches_with_indices)} items, {len(unmatched_indices)} unmatched")
            
            return {
                "matches": matches_with_indices,
                "unmatched": unmatched_indices,
                "raw_llm_response": result  # Keep for debugging
            }
            
        except Exception as e:
            logger.error(f"Fuzzy matching failed: {str(e)}", exc_info=True)
            raise Exception(f"Failed to match items: {str(e)}")

    def _find_index_by_id(self, items: List[Dict[str, Any]], id_key: str, target_id: str) -> Optional[int]:
        """Find the original index of an item by its ID"""
        for item in items:
            if item.get(id_key) == target_id:
                return item.get("original_index")
        return None


# Singleton instance
fuzzy_match_service = FuzzyMatchService()

