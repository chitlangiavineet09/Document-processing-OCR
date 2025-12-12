"""Service for extracting PO number from OCR payload using fuzzy matching"""
from typing import Optional, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)


class POExtractionService:
    """Service for extracting PO number from OCR payload"""

    def __init__(self):
        # Keywords to search for PO number (case-insensitive)
        self.po_keywords = [
            "purchase order",
            "po number",
            "po no",
            "order number",
            "order no",
            "buyer order number",
            "buyer order no",
            "purchase order number",
            "purchase order no",
            "po#",
            "order#",
        ]

    def extract_po_number(self, ocr_payload: Dict[str, Any]) -> Optional[str]:
        """
        Extract PO number from OCR payload using fuzzy matching.
        
        Args:
            ocr_payload: OCR extracted data dictionary
            
        Returns:
            PO number string if found, None otherwise
        """
        if not ocr_payload:
            return None

        # Strategy 1: Direct field lookup (most common patterns)
        po_fields = [
            "po_number", "poNumber", "po_number", "po_no",
            "order_number", "orderNumber", "order_no", "orderNo",
            "purchase_order_number", "purchaseOrderNumber",
            "buyer_order_number", "buyerOrderNumber",
            "purchase_order_no", "purchaseOrderNo",
            "po#", "order#", "po", "order"
        ]

        for field in po_fields:
            value = self._get_nested_value(ocr_payload, field)
            if value and self._is_valid_po(value):
                logger.info(f"Found PO number in field '{field}': {value}")
                return str(value).strip()

        # Strategy 2: Search in all text fields (fuzzy matching)
        text_content = self._extract_all_text(ocr_payload)
        
        if text_content:
            po_number = self._find_po_in_text(text_content)
            if po_number:
                logger.info(f"Found PO number via text search: {po_number}")
                return po_number

        # Strategy 3: Search in specific known fields like "items", "header", "details"
        for section in ["header", "invoice_header", "bill_header", "details", "summary"]:
            section_data = self._get_nested_value(ocr_payload, section)
            if section_data and isinstance(section_data, dict):
                for field in po_fields:
                    value = self._get_nested_value(section_data, field)
                    if value and self._is_valid_po(value):
                        logger.info(f"Found PO number in {section}.{field}: {value}")
                        return str(value).strip()

        logger.warning("Could not extract PO number from OCR payload")
        return None

    def _get_nested_value(self, data: Any, key: str) -> Any:
        """Get value from nested dictionary using dot notation or direct key"""
        if not isinstance(data, dict):
            return None

        # Try direct key first
        if key in data:
            return data[key]

        # Try case-insensitive search
        key_lower = key.lower()
        for k, v in data.items():
            if k.lower() == key_lower:
                return v

        # Try nested keys with dot notation
        if '.' in key:
            parts = key.split('.')
            current = data
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                    if current is None:
                        return None
                else:
                    return None
            return current

        return None

    def _extract_all_text(self, data: Any, max_depth: int = 5) -> str:
        """Recursively extract all text values from OCR payload"""
        if max_depth <= 0:
            return ""

        if isinstance(data, dict):
            texts = []
            for key, value in data.items():
                if isinstance(value, str):
                    texts.append(f"{key}: {value}")
                elif isinstance(value, (dict, list)):
                    nested_text = self._extract_all_text(value, max_depth - 1)
                    if nested_text:
                        texts.append(nested_text)
            return " ".join(texts)
        elif isinstance(data, list):
            texts = []
            for item in data:
                nested_text = self._extract_all_text(item, max_depth - 1)
                if nested_text:
                    texts.append(nested_text)
            return " ".join(texts)
        elif isinstance(data, str):
            return data

        return ""

    def _find_po_in_text(self, text: str) -> Optional[str]:
        """Find PO number in text using pattern matching"""
        if not text:
            return None

        text_lower = text.lower()

        # Look for PO keywords followed by a value
        for keyword in self.po_keywords:
            # Pattern 1: "PO Number: VALUE" or "PO Number VALUE"
            patterns = [
                rf"{re.escape(keyword)}\s*[:#\-]?\s*([A-Z0-9\-/]+)",
                rf"{re.escape(keyword)}\s+([A-Z0-9\-/]+)",
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    po_value = match.group(1).strip()
                    if self._is_valid_po(po_value):
                        return po_value

        # Pattern 2: Common PO number formats (alphanumeric with dashes/slashes)
        po_patterns = [
            r'\b([A-Z]{2,4}[\-]?[A-Z0-9]{3,}[\-]?[0-9]+)\b',  # PO-1234, PO1234
            r'\b([A-Z]{2,4}[\-][0-9]{4,})\b',  # PO-12345
            r'\b(ORD[\-]?[A-Z0-9]+)\b',  # ORD-1234
            r'\b(PO[\#]?[\s]?[0-9]{3,})\b',  # PO#1234, PO 1234
        ]

        for pattern in po_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                po_value = match.group(1).strip()
                if self._is_valid_po(po_value):
                    return po_value

        return None

    def _is_valid_po(self, value: Any) -> bool:
        """Validate if the value looks like a PO number"""
        if not value:
            return False

        value_str = str(value).strip()

        # Must have at least 3 characters
        if len(value_str) < 3:
            return False

        # Must contain at least one letter and one digit, or be a meaningful alphanumeric string
        has_letter = bool(re.search(r'[A-Za-z]', value_str))
        has_digit = bool(re.search(r'\d', value_str))

        # Valid if it has both letters and numbers, or is a long alphanumeric string
        if (has_letter and has_digit) or (has_letter and len(value_str) >= 5) or (has_digit and len(value_str) >= 4):
            # Exclude common false positives
            false_positives = ['date', 'amount', 'total', 'quantity', 'gst', 'tax', 'invoice']
            if value_str.lower() in false_positives:
                return False
            return True

        return False


# Singleton instance
po_extraction_service = POExtractionService()

