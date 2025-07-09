# src/schemas/vendor.py
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class BusinessTypeEnum(str, Enum):
    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    PARTNERSHIP = "partnership"
    PRIVATE_LIMITED = "private_limited"
    PUBLIC_LIMITED = "public_limited"
    LLP = "llp"
    ONE_PERSON_COMPANY = "one_person_company"
    TRUST = "trust"
    SOCIETY = "society"
    COOPERATIVE = "cooperative"
    OTHER = "other"

class VendorStatusEnum(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"

class VendorRegistrationRequest(BaseModel):
    # Personal Information
    owner_name: str = Field(..., min_length=2, max_length=255)
    phone_number: str = Field(..., regex=r'^[6-9]\d{9}$')
    email: EmailStr
    aadhar_number: str = Field(..., regex=r'^\d{12}$')
    
    # Business Information
    business_name: str = Field(..., min_length=2, max_length=255)
    business_type: BusinessTypeEnum
    business_description: Optional[str] = Field(None, max_length=2000)
    gst_number: Optional[str] = Field(None, regex=r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')
    pan_number: Optional[str] = Field(None, regex=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')
    
    # Address Information
    address_line_1: str = Field(..., min_length=5, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., regex=r'^\d{6}$')
    country: str = Field(default="India", max_length=100)
    
    # Bank Information
    bank_name: str = Field(..., min_length=2, max_length=255)
    account_number: str = Field(..., min_length=9, max_length=50)
    ifsc_code: str = Field(..., regex=r'^[A-Z]{4}0[A-Z0-9]{6}$')
    account_holder_name: str = Field(..., min_length=2, max_length=255)
    
    # Business Details (Optional)
    years_in_business: Optional[int] = Field(None, ge=0, le=100)
    # Terms and Conditions
    terms_accepted: bool = Field(..., const=True)
    
    @validator('email')
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('gst_number', pre=True)
    def validate_gst_number(cls, v):
        if v and v.strip():
            v = v.strip().upper()
            if len(v) != 15:
                raise ValueError('GST number must be 15 characters long')
            return v
        return None
    
    @validator('pan_number', pre=True)
    def validate_pan_number(cls, v):
        if v and v.strip():
            v = v.strip().upper()
            if len(v) != 10:
                raise ValueError('PAN number must be 10 characters long')
            return v
        return None
    
    @validator('ifsc_code', pre=True)
    def validate_ifsc_code(cls, v):
        if v:
            return v.strip().upper()
        return v
    
    @validator('postal_code')
    def validate_postal_code(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError('Postal code must be 6 digits')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "owner_name": "John Doe",
                "phone_number": "9876543210",
                "email": "john@example.com",
                "aadhar_number": "123456789012",
                "business_name": "John's Electronics",
                "business_type": "sole_proprietorship",
                "business_description": "We sell electronic gadgets and accessories",
                "gst_number": "22AAAAA0000A1Z5",
                "pan_number": "ABCDE1234F",
                "address_line_1": "123 Main Street",
                "address_line_2": "Near City Mall",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400001",
                "country": "India",
                "bank_name": "State Bank of India",
                "account_number": "1234567890",
                "ifsc_code": "SBIN0001234",
                "account_holder_name": "John Doe",
                "years_in_business": 5,
                "annual_turnover": 1000000.0,
                "number_of_employees": 10,
                "website_url": "https://johnselectronics.com",
                "business_license_number": "BL123456",
                "tax_registration_number": "TX789012",
                "terms_accepted": True
            }
        }

class VendorResponse(BaseModel):
    vendor_id: int
    vendor_code: str
    owner_name: str
    business_name: str
    business_type: str
    vendor_status: str
    email: str
    phone_number: str
    registration_date: datetime
    is_email_verified: bool
    is_phone_verified: bool
    is_documents_verified: bool
    is_bank_verified: bool
    
    class Config:
        from_attributes = True

class VendorDetailResponse(BaseModel):
    vendor_id: int
    vendor_code: str
    
    # Personal Information
    owner_name: str
    vendor_photo: Optional[str]
    phone_number: str
    email: str
    aadhar_number: str
    
    # Business Information
    business_name: str
    business_type: str
    business_description: Optional[str]
    gst_number: Optional[str]
    pan_number: Optional[str]
    
    # Address Information
    address_line_1: str
    address_line_2: Optional[str]
    city: str
    state: str
    postal_code: str
    country: str
    
    # Bank Information
    bank_name: Optional[str]
    account_number: Optional[str]
    ifsc_code: Optional[str]
    account_holder_name: Optional[str]
    
    # Business Details
    years_in_business: Optional[int]
    # System Information
    vendor_status: str
    registration_date: datetime
    approval_date: Optional[datetime]
    last_updated: datetime
    
    # Verification Status
    is_email_verified: bool
    is_phone_verified: bool
    is_documents_verified: bool
    is_bank_verified: bool
    
    # Admin fields (only for admin users)
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    class Config:
        from_attributes = True

class VendorRegistrationResponse(BaseModel):
    vendor_id: int
    vendor_code: str
    message: str
    status: str
    estimated_review_time: str = "2-3 business days"
    
    class Config:
        schema_extra = {
            "example": {
                "vendor_id": 1,
                "vendor_code": "VND20241225001",
                "message": "Registration submitted successfully! We will review your application and get back to you within 2-3 business days.",
                "status": "pending",
                "estimated_review_time": "2-3 business days"
            }
        }

class VendorListResponse(BaseModel):
    vendors: list[VendorResponse]
    total_count: int
    page: int
    size: int
    
class VendorStatusUpdate(BaseModel):
    status: VendorStatusEnum
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    
class VendorProfileUpdate(BaseModel):
    # Personal Information (updatable)
    owner_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone_number: Optional[str] = Field(None, regex=r'^[6-9]\d{9}$')
    
    # Business Information (updatable)
    business_name: Optional[str] = Field(None, min_length=2, max_length=255)
    business_description: Optional[str] = Field(None, max_length=2000)
    
    # Address Information (updatable)
    address_line_1: Optional[str] = Field(None, min_length=5, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    postal_code: Optional[str] = Field(None, regex=r'^\d{6}$')
    
    # Bank Information (updatable)
    bank_name: Optional[str] = Field(None, min_length=2, max_length=255)
    account_number: Optional[str] = Field(None, min_length=9, max_length=50)
    ifsc_code: Optional[str] = Field(None, regex=r'^[A-Z]{4}0[A-Z0-9]{6}$')
    account_holder_name: Optional[str] = Field(None, min_length=2, max_length=255)
    
    # Business Details (updatable)
    years_in_business: Optional[int] = Field(None, ge=0, le=100)
# Additional utility schemas
class VendorSearchFilters(BaseModel):
    business_type: Optional[BusinessTypeEnum] = None
    vendor_status: Optional[VendorStatusEnum] = None
    state: Optional[str] = None
    city: Optional[str] = None
    is_verified: Optional[bool] = None
    registration_date_from: Optional[datetime] = None
    registration_date_to: Optional[datetime] = None