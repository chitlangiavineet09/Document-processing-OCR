from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration"""
    IN_QUEUE = "in_queue"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"


class DocStatus(str, Enum):
    """Document status enumeration"""
    DRAFT_PENDING = "draft_pending"
    DRAFT_CREATED = "draft_created"
    UNKNOWN = "unknown"


class DocType(str, Enum):
    """Document type enumeration"""
    BILL = "bill"
    EWAY_BILL = "eway_bill"
    UNKNOWN = "unknown"


# Job Thread Schemas
class JobThreadCreate(BaseModel):
    """Schema for creating a new job thread"""
    file_name: str
    original_size: int
    user_id: str
    storage_path: Optional[str] = None


class JobThreadOut(BaseModel):
    """Schema for job thread response"""
    id: str
    user_id: str
    file_name: str
    original_size: int
    status: JobStatus
    storage_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class JobThreadSummary(BaseModel):
    """Schema for job thread summary (for listings)"""
    id: str
    file_name: str
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    document_count: Optional[int] = 0
    can_review_docs: bool = False


# Document Schemas
class DocOut(BaseModel):
    """Schema for document response"""
    id: str
    job_thread_id: str
    user_id: str
    page_number: int
    doc_type: DocType
    status: DocStatus
    ocr_payload: Optional[Dict[str, Any]] = None
    po_number: Optional[str] = None  # Extracted PO number
    items: Optional[List[Dict[str, Any]]] = None  # Extracted and formatted items
    storage_uri: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# File Upload Schemas
class FileUploadResponse(BaseModel):
    """Response schema for file upload"""
    job_id: str
    status: JobStatus
    message: str
    file_name: str


class JobUpdateResponse(BaseModel):
    """Response schema for job updates"""
    id: str
    file_name: str
    status: JobStatus
    updated_at: datetime
    error_message: Optional[str] = None


# Error Schemas
class ErrorResponse(BaseModel):
    """Standard error response schema"""
    detail: str
    error_code: Optional[str] = None


# Health Check Schemas
class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Draft Bill Schemas
class ConfirmPORequest(BaseModel):
    """Request schema for confirming PO number"""
    po_number: str = Field(..., min_length=1, description="Purchase Order number")


class ConfirmPOResponse(BaseModel):
    """Response schema for PO confirmation"""
    doc_id: str
    po_number: str
    order_mongo_id: str
    order_number: Optional[str] = None
    supplier_name: Optional[str] = None
    order_date: Optional[str] = None
    message: str


class MatchedItem(BaseModel):
    """Schema for a matched item"""
    bill_index: int
    order_index: int
    bill_item: Dict[str, Any]
    order_item: Dict[str, Any]
    item_name: str
    master_item_name: Optional[str] = None
    item_code: Optional[str] = None
    hsn: Optional[str] = None
    total_quantity: Optional[float] = None
    billable_quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_rate: Optional[float] = None
    gst_type: Optional[str] = None  # 'CGST-SGST' or 'IGST'
    available_tax_rates: Optional[List[float]] = None


class MatchItemsResponse(BaseModel):
    """Response schema for item matching"""
    doc_id: str
    matches: List[MatchedItem]
    unmatched_bill_items: List[Dict[str, Any]]
    validation_errors: Optional[List[str]] = None


class ItemInput(BaseModel):
    """Schema for item input from user"""
    bill_index: int
    order_index: int
    selected: bool = True
    quantity: float = Field(..., gt=0, description="Quantity")
    gst_rate: Optional[float] = Field(None, ge=0, le=100, description="GST rate percentage")
    cgst_rate: Optional[float] = Field(None, ge=0, le=100, description="CGST rate percentage (for CGST-SGST)")
    sgst_rate: Optional[float] = Field(None, ge=0, le=100, description="SGST rate percentage (for CGST-SGST)")


class SaveDraftRequest(BaseModel):
    """Request schema for saving draft bill"""
    items: List[ItemInput] = Field(..., min_items=1, description="List of items to include in draft")


class DraftBillOut(BaseModel):
    """Schema for draft bill response"""
    id: str
    doc_id: str
    job_thread_id: str
    user_id: str
    po_number: Optional[str] = None
    order_number: Optional[str] = None
    order_mongo_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DraftItemOut(BaseModel):
    """Schema for draft item response"""
    id: str
    draft_bill_id: str
    item_name: str
    master_item_name: Optional[str] = None
    item_code: Optional[str] = None
    hsn: Optional[str] = None
    total_quantity: Optional[float] = None
    billable_quantity: Optional[float] = None
    quantity: float
    gst_type: Optional[str] = None
    cgst_rate: Optional[float] = None
    sgst_rate: Optional[float] = None
    igst_rate: Optional[float] = None
    unit: Optional[str] = None
    unit_rate: Optional[float] = None
    amount: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class DraftBillDetailOut(BaseModel):
    """Schema for detailed draft bill response with items"""
    id: str
    doc_id: str
    job_thread_id: str
    user_id: str
    po_number: Optional[str] = None
    order_number: Optional[str] = None
    order_mongo_id: Optional[str] = None
    order_details: Optional[Dict[str, Any]] = None
    ocr_payload: Optional[Dict[str, Any]] = None  # OCR data from docs table (replaces extracted_data)
    items: List[DraftItemOut] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


class DraftBillSummaryOut(BaseModel):
    """Schema for draft bill summary (for listing)"""
    id: str
    doc_id: str
    po_number: Optional[str] = None
    order_number: Optional[str] = None
    created_at: datetime
    total_amount: Optional[float] = None
    item_count: int = 0
    
    class Config:
        from_attributes = True


# User Management Schemas (Admin)
class UserOut(BaseModel):
    """Schema for user response"""
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    deleted_at: Optional[str] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Schema for creating a user"""
    email: str
    password: str = Field(..., min_length=6, description="User password (minimum 6 characters)")
    full_name: Optional[str] = None
    role: Optional[str] = "user"  # Default to user role
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    
    class Config:
        from_attributes = True


# Settings Schemas
class SettingUpdate(BaseModel):
    """Schema for updating a setting"""
    value: str
    description: Optional[str] = None

