# src/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re

NAME_RE = re.compile(r"^[a-zA-Z\s\-']+$")


def _validate_password(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Za-z]", v):
        raise ValueError("Password must contain at least one letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one digit")
    return v


class SendOTPRequest(BaseModel):
    """Used internally by send-verification-otp / forgot-password — purpose is
    set by the calling endpoint, not the request body."""
    email: EmailStr = Field(..., description="Email address to receive the OTP")


class SendOTPResponse(BaseModel):
    success: bool
    message: str
    otp_id: str
    expires_in: int = Field(default=600, description="OTP expiry time in seconds")


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

    @validator('otp')
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        return v


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=2, max_length=255)

    @validator('password')
    def validate_password(cls, v):
        return _validate_password(v)

    @validator('name')
    def validate_name(cls, v):
        if not NAME_RE.match(v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator('otp')
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        return v

    @validator('new_password')
    def validate_password(cls, v):
        return _validate_password(v)


class CompleteRegistrationRequest(BaseModel):
    """Legacy: kept while older frontend code paths still call it."""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=255)

    @validator('name')
    def validate_name(cls, v):
        if not NAME_RE.match(v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return v.strip()


class AuthResponse(BaseModel):
    success: bool
    token: str
    refresh_token: Optional[str] = None
    user: dict
    expires_at: datetime
    is_new_user: bool = False


class PendingVerificationResponse(BaseModel):
    """Returned by /auth/login when the user's email is not yet verified.
    Frontend reads pending_verification=true and routes to the verify page."""
    success: bool = False
    pending_verification: bool = True
    email: EmailStr
    message: str = "Email verification required. We sent a fresh code to your inbox."


class GenericSuccessResponse(BaseModel):
    success: bool = True
    message: str


class CustomerResponse(BaseModel):
    customer_id: int
    customer_email: EmailStr
    customer_ph_no: Optional[str]
    customer_name: Optional[str]
    date_of_registration: datetime
    is_profile_complete: bool


PHONE_RE = re.compile(r"^[0-9]{10}$")


class UpdateProfileRequest(BaseModel):
    """Logged-in profile edit. Email is intentionally not editable here —
    changing it would require re-verification, which is a separate flow."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)

    @validator('name')
    def validate_name(cls, v):
        if v is None:
            return v
        if not NAME_RE.match(v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return v.strip()

    @validator('phone_number')
    def validate_phone(cls, v):
        if v is None or v == '':
            return None
        v = v.strip()
        if not PHONE_RE.match(v):
            raise ValueError('Phone number must be exactly 10 digits')
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator('new_password')
    def validate_new_password(cls, v):
        return _validate_password(v)