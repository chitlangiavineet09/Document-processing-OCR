"""Service for interacting with OMS APIs"""
from typing import Dict, Any, Optional, List
import httpx
import uuid
from app.core.config import settings
from app.services.settings_service import settings_service
import logging

logger = logging.getLogger(__name__)


class OMSService:
    """Service for interacting with OMS APIs"""

    def __init__(self):
        self.base_url = settings.OMS_API_BASE_URL
        # Get auth token from settings table or environment variable
        self.auth_token = self._get_auth_token()
        self.timeout = 30.0  # 30 seconds timeout

    def _get_auth_token(self) -> Optional[str]:
        """Get OMS auth token from settings table or environment variable"""
        try:
            # Try to get from settings table first
            oms_settings = settings_service._fetch_settings("oms_api")
            token = oms_settings.get("auth_token", None)
            if token and token.strip():
                return token.strip()
        except Exception as e:
            logger.warning(f"Failed to fetch OMS auth token from settings: {str(e)}")

        # Fall back to environment variable
        return settings.OMS_AUTH_TOKEN

    def _get_headers(self) -> Dict[str, str]:
        """Get default headers for OMS API requests"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Automatic-Bill-Processing-System/1.0",
        }
        
        if self.auth_token:
            headers["authorizationtoken"] = self.auth_token

        return headers

    async def get_order_by_po_number(self, po_number: str) -> Dict[str, Any]:
        """
        Get order mongo ID from PO number using OMS API1.
        
        Args:
            po_number: Purchase Order number to search for
            
        Returns:
            Dictionary containing order details from API response
            
        Raises:
            Exception: If API call fails or no order found
        """
        try:
            if not po_number or not po_number.strip():
                raise ValueError("PO number cannot be empty")

            if not self.auth_token:
                raise Exception("OMS API auth token not configured. Please configure it in Settings.")

            # OMS API1: Get order list by PO number
            url = f"{self.base_url}/orders/order-list/order-listV2"
            params = {
                "false": "null",
                "pageNumber": 1,
                "searchText": po_number.strip()
            }

            headers = self._get_headers()
            # Add additional headers as per PRD
            headers.update({
                "X-Request-Id": str(uuid.uuid4()),
                "sec-ch-ua-platform": '"macOS"',
                "Referer": "https://oms.zetwerk.com/",
                "timezone": "Asia/Calcutta",
                "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "X-COMPANY-SLUG": "zetwerk",
                "X-Service-Version": "1.0.1",
                "x-tenant-id": "65a8375f661b21baf0339f2f",  # Can be configured later
                "ngsw-bypass": "true"
            })

            logger.info(f"Calling OMS API1 to search for PO: {po_number}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                # Check if response is successful
                if not data.get("success") or data.get("status") != 200:
                    error_msg = data.get("message", "Unknown error from OMS API")
                    raise Exception(f"OMS API error: {error_msg}")

                # Check if orders were found
                all_documents = data.get("data", {}).get("allDocuments", [])
                if not all_documents:
                    raise Exception(f"No order found for PO number: {po_number}")

                # Return the first matching order
                order = all_documents[0]
                logger.info(f"Found order: {order.get('orderNumber')} with mongo ID: {order.get('_id')}")
                
                return order

        except httpx.HTTPStatusError as e:
            logger.error(f"OMS API HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"OMS API returned error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"OMS API request error: {str(e)}")
            raise Exception(f"Failed to connect to OMS API: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting order by PO number: {str(e)}")
            raise

    async def get_order_details(self, order_mongo_id: str) -> Dict[str, Any]:
        """
        Get full order details from OMS API2.
        
        Args:
            order_mongo_id: MongoDB ID of the order
            
        Returns:
            Dictionary containing full order details from API response
            
        Raises:
            Exception: If API call fails
        """
        try:
            if not order_mongo_id or not order_mongo_id.strip():
                raise ValueError("Order mongo ID cannot be empty")

            if not self.auth_token:
                raise Exception("OMS API auth token not configured. Please configure it in Settings.")

            # OMS API2: Get order details by mongo ID
            url = f"{self.base_url}/orders/{order_mongo_id.strip()}"
            headers = self._get_headers()
            
            # Add the same additional headers as OMS API1
            headers.update({
                "X-Request-Id": str(uuid.uuid4()),
                "sec-ch-ua-platform": '"macOS"',
                "Referer": "https://oms.zetwerk.com/",
                "timezone": "Asia/Calcutta",
                "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "X-COMPANY-SLUG": "zetwerk",
                "X-Service-Version": "1.0.1",
                "x-tenant-id": "65a8375f661b21baf0339f2f",  # Can be configured later
                "ngsw-bypass": "true"
            })

            logger.info(f"Calling OMS API2 to get order details: {order_mongo_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                logger.info(f"Retrieved order details for: {order_mongo_id}")
                
                return data

        except httpx.HTTPStatusError as e:
            logger.error(f"OMS API HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"OMS API returned error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"OMS API request error: {str(e)}")
            raise Exception(f"Failed to connect to OMS API: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting order details: {str(e)}")
            raise


# Singleton instance
oms_service = OMSService()

