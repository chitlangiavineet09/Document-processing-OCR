"""Service for extracting items from OCR payload"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ItemsExtractionService:
    """Service for extracting items from OCR payload and formatting them"""

    def extract_items(self, ocr_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract items from OCR payload and format them for storage.
        
        Args:
            ocr_payload: OCR extracted data dictionary
            
        Returns:
            List of formatted item dictionaries
        """
        if not ocr_payload:
            return []

        # Try multiple possible field names for items
        items = ocr_payload.get("items", [])
        if not items:
            items = ocr_payload.get("lineItems", []) or ocr_payload.get("line_items", []) or []

        if not items or not isinstance(items, list):
            logger.warning("No items found in OCR payload or items is not a list")
            return []

        # Format items for storage
        formatted_items = []
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                logger.warning(f"Item at index {idx} is not a dictionary, skipping")
                continue

            # Extract and format item data
            formatted_item = {
                "billId": f"b{idx}",  # Temporary ID for matching
                "name": self._extract_field(item, ["name", "itemName", "item_name", "description", "productName", "product_name", "itemDescription"]),
                "hsn_sac": self._extract_hsn_sac(item),  # Can be HSN or SAC
                "quantity": self._extract_field(item, ["quantity", "qty", "Quantity", "amount", "qtyValue"]),
                "unit": self._extract_field(item, ["unit", "uom", "unitOfMeasure", "Unit"]),
                "rate": self._extract_field(item, ["rate", "unitRate", "unit_rate", "price", "unitPrice", "ratePerUnit"]),
                "amount": self._extract_field(item, ["amount", "total", "totalAmount", "itemTotal", "lineTotal"]),
                "tax_rate": self._extract_field(item, ["taxRate", "tax_rate", "gstRate", "gst_rate", "tax"]),
                "cgst": self._extract_field(item, ["cgst", "CGST", "cgstRate", "cgst_rate"]),
                "sgst": self._extract_field(item, ["sgst", "SGST", "sgstRate", "sgst_rate"]),
                "igst": self._extract_field(item, ["igst", "IGST", "igstRate", "igst_rate"]),
                "discount": self._extract_field(item, ["discount", "Discount", "discountAmount", "discount_amount"]),
                # Store original item for reference
                "rawItem": item
            }
            
            formatted_items.append(formatted_item)

        logger.info(f"Extracted {len(formatted_items)} items from OCR payload")
        return formatted_items

    def _extract_field(self, item: Dict[str, Any], field_names: List[str]) -> Optional[Any]:
        """Extract field value trying multiple possible field names"""
        for field_name in field_names:
            value = item.get(field_name)
            if value is not None and value != "":
                return value
        return None

    def _extract_hsn_sac(self, item: Dict[str, Any]) -> Optional[str]:
        """Extract HSN or SAC code (can be either)"""
        # Try HSN fields first
        hsn_fields = ["hsn", "hsnCode", "hsn_code", "HSN", "HSNCode", "hsnSac", "hsn_sac"]
        for field in hsn_fields:
            value = item.get(field)
            if value is not None and value != "":
                return str(value)
        
        # Try SAC fields
        sac_fields = ["sac", "sacCode", "sac_code", "SAC", "SACCode"]
        for field in sac_fields:
            value = item.get(field)
            if value is not None and value != "":
                return str(value)
        
        return None


# Singleton instance
items_extraction_service = ItemsExtractionService()

