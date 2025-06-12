# src/schemas/auth.py
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re

class SendOTPRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number with country code")
    country_code: str = Field(..., description="Country code like +1, +91")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', v)
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError('Phone number must be between 10 and 15 digits')
        return cleaned

class SendOTPResponse(BaseModel):
    success: bool
    message: str
    otp_id: str
    expires_in: int = Field(default=600, description="OTP expiry time in seconds")

class VerifyOTPRequest(BaseModel):
    phone_number: str
    otp: str = Field(..., min_length=6, max_length=6)
    
    @validator('otp')
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        return v

class CompleteRegistrationRequest(BaseModel):
    phone_number: str
    name: str = Field(..., min_length=2, max_length=255)
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return v.strip()

class AuthResponse(BaseModel):
    success: bool
    token: str
    refresh_token: Optional[str] = None
    user: dict
    expires_at: datetime
    is_new_user: bool = False

class CustomerResponse(BaseModel):
    customer_id: int
    customer_ph_no: str
    customer_name: Optional[str]
    date_of_registration: datetime
    is_profile_complete: bool