"""Draft bill endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
import logging
import json
from datetime import datetime
import uuid

from app.core.auth import get_current_user
from app.services.database import get_supabase_client
from app.services.oms_service import oms_service
from app.services.fuzzy_match_service import fuzzy_match_service
from app.services.redis_service import redis_service
from app.models.schemas import (
    ConfirmPORequest,
    ConfirmPOResponse,
    MatchItemsResponse,
    MatchedItem,
    SaveDraftRequest,
    DraftBillOut,
    DraftBillDetailOut,
    DraftBillSummaryOut,
    DraftItemOut,
    DocType,
    DocStatus
)

logger = logging.getLogger(__name__)
router = APIRouter()


def get_session_key(doc_id: str) -> str:
    """Get Redis session key for draft"""
    return f"draft_session:{doc_id}"


@router.get("", response_model=List[DraftBillSummaryOut], status_code=status.HTTP_200_OK)
async def list_draft_bills(
    user: dict = Depends(get_current_user)
):
    """
    List all draft bills for the current user (Created Draft Bills page).
    Returns summary with total amount and item count.
    """
    user_id = user["user_id"]
    
    try:
        supabase = get_supabase_client()
        
        # Get all draft bills for user
        draft_result = supabase.table("draft_bills").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        if not draft_result.data:
            return []
        
        # Get items for each draft bill and calculate totals
        summaries = []
        for draft_bill in draft_result.data:
            draft_bill_id = draft_bill["id"]
            
            # Get items for this draft bill
            items_result = supabase.table("items").select("amount").eq("draft_bill_id", draft_bill_id).execute()
            
            items = items_result.data if items_result.data else []
            total_amount = sum(float(item["amount"]) for item in items if item.get("amount"))
            item_count = len(items)
            
            created_at = datetime.fromisoformat(draft_bill["created_at"].replace("Z", "+00:00"))
            
            summaries.append(DraftBillSummaryOut(
                id=draft_bill["id"],
                doc_id=draft_bill["doc_id"],
                po_number=draft_bill.get("po_number"),
                order_number=draft_bill.get("order_number"),
                created_at=created_at,
                total_amount=total_amount if total_amount > 0 else None,
                item_count=item_count
            ))
        
        return summaries
        
    except Exception as e:
        logger.error(f"Error listing draft bills: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve draft bills: {str(e)}"
        )


@router.post("/{doc_id}/confirm-po", response_model=ConfirmPOResponse, status_code=status.HTTP_200_OK)
async def confirm_po(
    doc_id: str,
    request: ConfirmPORequest,
    user: dict = Depends(get_current_user)
):
    """
    Step 1: Confirm PO number and fetch order details.
    Creates a temporary draft session in Redis.
    """
    user_id = user["user_id"]
    
    try:
        supabase = get_supabase_client()
        
        # Verify document exists and belongs to user
        doc_result = supabase.table("docs").select("*").eq("id", doc_id).eq("user_id", user_id).single().execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or not authorized"
            )
        
        doc = doc_result.data
        
        # Verify document is a bill and in draft_pending status
        if doc["doc_type"] != DocType.BILL.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot create draft for document type: {doc['doc_type']}"
            )
        
        if doc["status"] != DocStatus.DRAFT_PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document status is {doc['status']}, expected draft_pending"
            )
        
        # Validate PO number
        po_number = request.po_number.strip()
        if not po_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PO number cannot be empty"
            )
        
        # Update PO number in doc table
        try:
            supabase.table("docs").update({
                "po_number": po_number,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", doc_id).execute()
            logger.info(f"Updated PO number {po_number} in doc {doc_id}")
        except Exception as e:
            logger.warning(f"Failed to update PO number in doc: {str(e)}")
            # Continue with OMS API call even if update fails
        
        # Call OMS API to get order by PO number
        try:
            order_summary = await oms_service.get_order_by_po_number(po_number)
            order_mongo_id = order_summary.get("_id")
            
            if not order_mongo_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Order not found for PO number: {po_number}"
                )
            
            # Get full order details
            order_details = await oms_service.get_order_details(order_mongo_id)
            
            # Store draft session in Redis
            session_key = get_session_key(doc_id)
            session_data = {
                "doc_id": doc_id,
                "user_id": user_id,
                "job_thread_id": doc["job_thread_id"],
                "po_number": po_number,
                "order_mongo_id": order_mongo_id,
                "order_number": order_summary.get("orderNumber"),
                "order_summary": order_summary,
                "order_details": order_details,
                "created_at": datetime.utcnow().isoformat()
            }
            
            redis_service.set_draft_session(session_key, session_data)
            
            return ConfirmPOResponse(
                doc_id=doc_id,
                po_number=po_number,
                order_mongo_id=order_mongo_id,
                order_number=order_summary.get("orderNumber"),
                supplier_name=order_summary.get("supplierName"),
                order_date=order_summary.get("poDate"),
                message="PO confirmed successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to confirm PO: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to confirm PO: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in confirm_po: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{doc_id}/match-items", response_model=MatchItemsResponse, status_code=status.HTTP_200_OK)
async def match_items(
    doc_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Step 2: Match bill items with order items using fuzzy matching.
    Returns matched items and unmatched bill items.
    """
    user_id = user["user_id"]
    
    try:
        supabase = get_supabase_client()
        
        # Verify document exists and belongs to user
        doc_result = supabase.table("docs").select("*").eq("id", doc_id).eq("user_id", user_id).single().execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or not authorized"
            )
        
        doc = doc_result.data
        
        # Get bill items from docs.items column (extracted and formatted during OCR)
        bill_items = doc.get("items", [])
        
        logger.info(f"Document {doc_id} - Found {len(bill_items)} bill items in docs.items column")
        
        if not bill_items:
            logger.error(f"No bill items found in docs.items column for doc {doc_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No items found in document. Please ensure the bill contains itemized details and was processed correctly."
            )
        
        # Get draft session from Redis
        session_key = get_session_key(doc_id)
        session_data = redis_service.get_draft_session(session_key)
        
        if not session_data:
            logger.error(f"Draft session not found for doc {doc_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Draft session not found. Please confirm PO number first."
            )
        
        logger.info(f"Session data keys: {list(session_data.keys())}")
        
        # Extract order items from order details
        order_details = session_data.get("order_details", {})
        logger.info(f"Order details type: {type(order_details)}, keys: {list(order_details.keys()) if isinstance(order_details, dict) else 'Not a dict'}")
        
        # OMS API2 response might be wrapped in a structure like:
        # { "success": true, "statusCode": 200, "message": "...", "data": { ... } }
        # Extract the actual order data from the 'data' field if it exists
        order_data = order_details
        if isinstance(order_details, dict) and "data" in order_details:
            order_data = order_details.get("data", {})
            logger.info(f"Extracted order data from wrapped response. Order data keys: {list(order_data.keys()) if isinstance(order_data, dict) else 'Not a dict'}")
        
        # Try multiple possible field names for items
        # Items are in: orderPODetails.items (as confirmed by user)
        order_items = []
        if isinstance(order_data, dict):
            # Try orderPODetails.items first (confirmed location)
            order_po_details = order_data.get("orderPODetails", {})
            if isinstance(order_po_details, dict):
                logger.info(f"Found orderPODetails. Keys: {list(order_po_details.keys())}")
                order_items = order_po_details.get("items", []) or order_po_details.get("orderItems", []) or []
                if order_items:
                    logger.info(f"Found {len(order_items)} items in orderPODetails.items")
            
            # Try direct items field as fallback
            if not order_items:
                order_items = order_data.get("items", []) or order_data.get("orderItems", []) or []
                if order_items:
                    logger.info(f"Found {len(order_items)} items in direct items field")
            
            # Try boqDetails.items if not found in previous locations
            if not order_items:
                boq_details = order_data.get("boqDetails", {})
                if isinstance(boq_details, dict):
                    logger.info(f"Found boqDetails. Keys: {list(boq_details.keys()) if isinstance(boq_details, dict) else 'Not a dict'}")
                    order_items = boq_details.get("items", []) or boq_details.get("orderItems", []) or []
                    if order_items:
                        logger.info(f"Found {len(order_items)} items in boqDetails.items")
        
        logger.info(f"Total found: {len(order_items)} order items in order details")
        
        if not order_items:
            # Log the full structure for debugging
            logger.error(f"No order items found. Order details structure: {json.dumps(order_details, indent=2, default=str)[:2000]}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No items found in order details. The order may not have items, or the structure is different than expected."
            )
        
        # Perform fuzzy matching
        try:
            match_result = fuzzy_match_service.match_items(bill_items, order_items)
        except Exception as e:
            logger.error(f"Fuzzy matching failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to match items: {str(e)}"
            )
        
        matches = match_result.get("matches", [])
        unmatched_indices = match_result.get("unmatched", [])
        
        # Build matched items response
        matched_items = []
        for match in matches:
            bill_item = match["billItem"]
            order_item = match["orderItem"]
            
            # Determine GST type from order item
            cgst = order_item.get("cgst")
            sgst = order_item.get("sgst")
            igst = order_item.get("igst")
            
            gst_type = None
            if (cgst is not None or sgst is not None) and igst is None:
                gst_type = "CGST-SGST"
            elif igst is not None and (cgst is None and sgst is None):
                gst_type = "IGST"
            
            # Get available tax rates (unique taxes from order item)
            available_tax_rates = []
            taxes = order_item.get("taxes", [])
            if taxes:
                available_tax_rates = list(set([float(tax.get("rate", 0)) for tax in taxes if tax.get("rate")]))
            
            # Extract quantities
            total_qty = order_item.get("quantity")
            billable_qty = order_item.get("unassignedQuantity") or order_item.get("unassigned_quantity")
            
            matched_items.append(MatchedItem(
                bill_index=match["billIndex"],
                order_index=match["orderIndex"],
                bill_item=bill_item,
                order_item=order_item,
                item_name=order_item.get("name") or order_item.get("masterItemName", ""),
                master_item_name=order_item.get("masterItemName"),
                item_code=order_item.get("itemCode"),
                hsn=order_item.get("hsnCode"),
                total_quantity=float(total_qty) if total_qty else None,
                billable_quantity=float(billable_qty) if billable_qty else None,
                unit=order_item.get("unit"),
                unit_rate=float(order_item.get("unitRate") or order_item.get("unit_rate") or 0),
                gst_type=gst_type,
                available_tax_rates=available_tax_rates
            ))
        
        # Get unmatched bill items
        unmatched_bill_items = [bill_items[idx] for idx in unmatched_indices if idx < len(bill_items)]
        
        # Validation errors
        validation_errors = []
        if unmatched_bill_items:
            validation_errors.append(f"{len(unmatched_bill_items)} bill item(s) could not be matched to order items")
        
        # Store match result in session for later use
        session_data["matched_items"] = [m.dict() for m in matched_items]
        session_data["unmatched_items"] = unmatched_bill_items
        redis_service.set_draft_session(session_key, session_data)
        
        return MatchItemsResponse(
            doc_id=doc_id,
            matches=matched_items,
            unmatched_bill_items=unmatched_bill_items,
            validation_errors=validation_errors if validation_errors else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in match_items: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{doc_id}/save", response_model=DraftBillOut, status_code=status.HTTP_201_CREATED)
async def save_draft(
    doc_id: str,
    request: SaveDraftRequest,
    user: dict = Depends(get_current_user)
):
    """
    Step 3: Save draft bill and items to database.
    Creates draft_bill and items records atomically.
    """
    user_id = user["user_id"]
    
    try:
        supabase = get_supabase_client()
        
        # Verify document exists and belongs to user
        doc_result = supabase.table("docs").select("*").eq("id", doc_id).eq("user_id", user_id).single().execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or not authorized"
            )
        
        doc = doc_result.data
        
        # Get draft session from Redis
        session_key = get_session_key(doc_id)
        session_data = redis_service.get_draft_session(session_key)
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Draft session expired. Please start over from PO confirmation."
            )
        
        # Validate items
        if not request.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one item is required"
            )
        
        matched_items = session_data.get("matched_items", [])
        
        # Create draft_bill record
        draft_bill_id = str(uuid.uuid4())
        draft_bill_data = {
            "id": draft_bill_id,
            "doc_id": doc_id,
            "job_thread_id": session_data["job_thread_id"],
            "user_id": user_id,
            "po_number": session_data["po_number"],
            "order_number": session_data.get("order_number"),
            "order_mongo_id": session_data["order_mongo_id"],
            "order_details": session_data["order_details"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Create items records
        items_data = []
        for item_input in request.items:
            if not item_input.selected:
                continue
            
            # Find the matched item
            matched_item = None
            for m in matched_items:
                if m["bill_index"] == item_input.bill_index and m["order_index"] == item_input.order_index:
                    matched_item = m
                    break
            
            if not matched_item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item not found for bill_index {item_input.bill_index} and order_index {item_input.order_index}"
                )
            
            order_item = matched_item["order_item"]
            
            # Validate quantity
            billable_qty = matched_item.get("billable_quantity") or 0
            if item_input.quantity > billable_qty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Quantity {item_input.quantity} exceeds billable quantity {billable_qty} for item {matched_item.get('item_name')}"
                )
            
            # Calculate amount
            unit_rate = matched_item.get("unit_rate") or 0
            gst_type = matched_item.get("gst_type")
            
            # Determine GST rates
            cgst_rate = None
            sgst_rate = None
            igst_rate = None
            
            if gst_type == "CGST-SGST":
                cgst_rate = item_input.cgst_rate or 0
                sgst_rate = item_input.sgst_rate or 0
                total_gst_rate = cgst_rate + sgst_rate
            elif gst_type == "IGST":
                igst_rate = item_input.gst_rate or 0
                total_gst_rate = igst_rate
            else:
                total_gst_rate = 0
            
            # Amount = (quantity * unit_rate) * (1 + GST_rate/100)
            amount = (item_input.quantity * unit_rate) * (1 + total_gst_rate / 100)
            
            items_data.append({
                "id": str(uuid.uuid4()),
                "draft_bill_id": draft_bill_id,
                "item_name": matched_item.get("item_name", ""),
                "master_item_name": matched_item.get("master_item_name"),
                "item_code": matched_item.get("item_code"),
                "hsn": matched_item.get("hsn"),
                "total_quantity": matched_item.get("total_quantity"),
                "billable_quantity": matched_item.get("billable_quantity"),
                "quantity": item_input.quantity,
                "gst_type": gst_type,
                "cgst_rate": cgst_rate,
                "sgst_rate": sgst_rate,
                "igst_rate": igst_rate,
                "unit": matched_item.get("unit"),
                "unit_rate": unit_rate,
                "amount": amount,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })
        
        if not items_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No items selected to save"
            )
        
        # Insert draft_bill and items atomically (using transaction-like behavior)
        try:
            # Insert draft_bill
            draft_result = supabase.table("draft_bills").insert(draft_bill_data).execute()
            
            if not draft_result.data:
                raise Exception("Failed to create draft_bill")
            
            # Insert items
            items_result = supabase.table("items").insert(items_data).execute()
            
            if not items_result.data:
                # Try to rollback draft_bill
                supabase.table("draft_bills").delete().eq("id", draft_bill_id).execute()
                raise Exception("Failed to create items")
            
            # Update doc status to draft_created
            supabase.table("docs").update({
                "status": DocStatus.DRAFT_CREATED.value,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", doc_id).execute()
            
            # Clear draft session from Redis
            redis_service.delete_draft_session(session_key)
            
            logger.info(f"Created draft bill {draft_bill_id} with {len(items_data)} items")
            
            return DraftBillOut(
                id=draft_bill_id,
                doc_id=doc_id,
                job_thread_id=session_data["job_thread_id"],
                user_id=user_id,
                po_number=session_data["po_number"],
                order_number=session_data.get("order_number"),
                order_mongo_id=session_data["order_mongo_id"],
                created_at=datetime.fromisoformat(draft_bill_data["created_at"].replace("Z", "+00:00"))
            )
            
        except Exception as e:
            logger.error(f"Failed to save draft: {str(e)}", exc_info=True)
            # Try to clean up if draft_bill was created
            try:
                supabase.table("draft_bills").delete().eq("id", draft_bill_id).execute()
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save draft: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in save_draft: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{doc_id}/final", response_model=DraftBillDetailOut, status_code=status.HTTP_200_OK)
async def get_draft_bill_detail(
    doc_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get final draft bill details by doc_id (Page 7).
    Returns draft bill with all items.
    """
    user_id = user["user_id"]
    
    try:
        supabase = get_supabase_client()
        
        # Verify document exists and belongs to user (we need this to get ocr_payload)
        doc_result = supabase.table("docs").select("*").eq("id", doc_id).eq("user_id", user_id).single().execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or not authorized"
            )
        
        doc = doc_result.data
        ocr_payload = doc.get("ocr_payload")  # Get OCR data from doc table
        
        # Get draft bill for this doc
        draft_result = supabase.table("draft_bills").select("*").eq("doc_id", doc_id).eq("user_id", user_id).single().execute()
        
        if not draft_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft bill not found for this document"
            )
        
        draft_bill = draft_result.data
        
        # Get items for this draft bill
        items_result = supabase.table("items").select("*").eq("draft_bill_id", draft_bill["id"]).order("created_at").execute()
        
        items = []
        if items_result.data:
            for item_data in items_result.data:
                created_at = datetime.fromisoformat(item_data["created_at"].replace("Z", "+00:00"))
                items.append(DraftItemOut(
                    id=item_data["id"],
                    draft_bill_id=item_data["draft_bill_id"],
                    item_name=item_data["item_name"],
                    master_item_name=item_data.get("master_item_name"),
                    item_code=item_data.get("item_code"),
                    hsn=item_data.get("hsn"),
                    total_quantity=float(item_data["total_quantity"]) if item_data.get("total_quantity") else None,
                    billable_quantity=float(item_data["billable_quantity"]) if item_data.get("billable_quantity") else None,
                    quantity=float(item_data["quantity"]),
                    gst_type=item_data.get("gst_type"),
                    cgst_rate=float(item_data["cgst_rate"]) if item_data.get("cgst_rate") else None,
                    sgst_rate=float(item_data["sgst_rate"]) if item_data.get("sgst_rate") else None,
                    igst_rate=float(item_data["igst_rate"]) if item_data.get("igst_rate") else None,
                    unit=item_data.get("unit"),
                    unit_rate=float(item_data["unit_rate"]) if item_data.get("unit_rate") else None,
                    amount=float(item_data["amount"]),
                    created_at=created_at
                ))
        
        created_at = datetime.fromisoformat(draft_bill["created_at"].replace("Z", "+00:00"))
        
        return DraftBillDetailOut(
            id=draft_bill["id"],
            doc_id=draft_bill["doc_id"],
            job_thread_id=draft_bill["job_thread_id"],
            user_id=draft_bill["user_id"],
            po_number=draft_bill.get("po_number"),
            order_number=draft_bill.get("order_number"),
            order_mongo_id=draft_bill.get("order_mongo_id"),
            order_details=draft_bill.get("order_details"),
            ocr_payload=ocr_payload,  # Use OCR payload from doc table instead of extracted_data
            items=items,
            created_at=created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting draft bill detail: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve draft bill: {str(e)}"
        )

