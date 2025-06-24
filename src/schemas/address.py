# src/schemas/address.py
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class CustomerAddressBase(BaseModel):
    address_type: str
    full_name: str
    phone_number: str
    pincode: str
    address_line1: str
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    state: str
    is_default: bool = False
    
    @validator('address_type')
    def validate_address_type(cls, v):
        if v not in ['home', 'office']:
            raise ValueError('Address type must be either "home" or "office"')
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError('Phone number must be 10 digits')
        return v
    
    @validator('pincode')
    def validate_pincode(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError('Pincode must be 6 digits')
        return v

class CustomerAddressCreate(CustomerAddressBase):
    pass

class CustomerAddressUpdate(BaseModel):
    address_type: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    pincode: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_default: Optional[bool] = None

class CustomerAddressResponse(CustomerAddressBase):
    address_id: int
    customer_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class AddressListResponse(BaseModel):
    addresses: list[CustomerAddressResponse]
    total_count: int
