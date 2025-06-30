

# src/api/v1/vender_auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Header, Form, File, UploadFile
# from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
from config.database import get_db
from src.schemas.vendor_auth import (
    SendOTPRequest, SendOTPResponse,
    VerifyOTPRequest, AuthResponse,
    CompleteRegistrationRequest,
    CompleteRegistrationForm
)
from src.services.auth_vendor_service import AuthVendorService
from src.models.vendor import Vendor as Customer

router = APIRouter()

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Customer:
    """Get current authenticated user from JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Extract token from "Bearer <token>"
        parts = authorization.split()
        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        scheme, token = parts
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify token
        payload = AuthVendorService.verify_token(token)
        vendor_id = payload.get("sub")
        
        if not vendor_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get customer from database
        customer = db.query(Customer).filter(
            Customer.vendor_id == int(vendor_id)
        ).first()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return customer
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.post("/auth/send-otp", response_model=SendOTPResponse)
async def send_otp(
    request: SendOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Send OTP to the provided phone number.
    
    For testing purposes, the OTP is always '123456'.
    In production, this would integrate with an SMS service.
    """
    return AuthVendorService.send_otp(request, db)

@router.post("/auth/verify-otp", response_model=AuthResponse)
async def verify_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Verify OTP and authenticate the user.
    
    If the phone number is new, a customer record is created without a name.
    The frontend should check is_new_user flag and prompt for name if true.
    """
    return AuthVendorService.verify_otp(request, db)

# @router.post("/auth/complete-registration")
# async def complete_registration(
#     request: CompleteRegistrationRequest,
#     current_user: Customer = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Complete registration by adding the customer's name.
    
#     This endpoint is called after OTP verification for new users.
#     Requires authentication token from verify-otp response.
#     """
#     return AuthVendorService.complete_registration(
#         request, 
#         current_user.vendor_id, 
#         db
#     )


# @router.post("/auth/complete-registration")
# async def complete_registration(
#     phone_number: str = Form(...),
#     name: str = Form(...),
#     email: Optional[str] = Form(None),
#     aadhar_number: str = Form(...),
#     personal_address: str = Form(...),
#     business_name: str = Form(...),
#     business_type: str = Form(...),
#     gst_number: Optional[str] = Form(None),
#     business_address: str = Form(...),
#     account_holder_name: str = Form(...),
#     account_number: str = Form(...),
#     ifsc_code: str = Form(...),
#     vendor_photo: UploadFile = File(None),

#     current_user: Customer = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     # Validate form fields using Pydantic
#     form_data = CompleteRegistrationForm(
#         phone_number=phone_number,
#         name=name,
#         email=email,
#         aadhar_number=aadhar_number,
#         personal_address=personal_address,
#         business_name=business_name,
#         business_type=business_type,
#         gst_number=gst_number,
#         business_address=business_address,
#         account_holder_name=account_holder_name,
#         account_number=account_number,
#         ifsc_code=ifsc_code
#     )

#     return AuthVendorService.complete_registration(
#         data=form_data.dict(),
#         vendor_id=current_user.vendor_id,
#         db=db,
#         vendor_photo=vendor_photo
#     )


@router.post("/auth/complete-registration")
async def complete_registration(
    phone_number: str = Form(...),
    name: str = Form(...),
    email: Optional[str] = Form(None),
    aadhar_number: str = Form(...),

    address_line1: str = Form(...),
    address_line2: Optional[str] = Form(""),
    district: str = Form(...),
    state: str = Form(...),
    pincode: str = Form(...),

    business_name: str = Form(...),
    business_type: str = Form(...),
    gst_number: Optional[str] = Form(None),
    business_address: str = Form(...),
    account_holder_name: str = Form(...),
    account_number: str = Form(...),
    ifsc_code: str = Form(...),
    vendor_photo: UploadFile = File(None),

    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    form_data = CompleteRegistrationForm(
        phone_number=phone_number,
        name=name,
        email=email,
        aadhar_number=aadhar_number,
        address_line1=address_line1,
        address_line2=address_line2,
        district=district,
        state=state,
        pincode=pincode,
        business_name=business_name,
        business_type=business_type,
        gst_number=gst_number,
        business_address=business_address,
        account_holder_name=account_holder_name,
        account_number=account_number,
        ifsc_code=ifsc_code
    )

    return AuthVendorService.complete_registration(
        data=form_data.dict(),
        vendor_id=current_user.vendor_id,
        db=db,
        vendor_photo=vendor_photo
    )
# @router.get("/auth/me")
# async def get_current_user_info(
#     current_user: Customer = Depends(get_current_user)
# ):
#     """
#     Get current authenticated user information.
    
#     Requires valid JWT token in Authorization header.
#     """
#     return {
#         "vendor_id": current_user.vendor_id,
#         "phone_number": current_user.vendor_ph_no,
#         "name": current_user.vendor_name,
#         "is_verified": True,
#         "created_at": current_user.date_of_registration.isoformat(),
#         "is_profile_complete": current_user.vendor_name is not None
#     }


@router.get("/auth/me")
async def get_current_user_info(
    current_user: Customer = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    Requires valid JWT token in Authorization header.
    """
    return {
        "vendor_id": current_user.vendor_id,
        "phone_number": current_user.vendor_ph_no,
        "name": current_user.vendor_name,
        "email": current_user.vendor_email,
        "aadhar_number": current_user.aadhar_number,
        "personal_address": current_user.personal_address,
        "business_name": current_user.business_name,
        "business_type": current_user.business_type,
        "gst_number": current_user.gst_number,
        "business_address": current_user.business_address,
        "account_holder_name": current_user.account_holder_name,
        "account_number": current_user.account_number,
        "ifsc_code": current_user.ifsc_code,
        "vendor_photo_path": current_user.vendor_photo_path,
        "is_verified": True,
        "is_profile_complete": current_user.vendor_name is not None,
        "created_at": current_user.date_of_registration.isoformat()
    }


@router.post("/auth/logout")
async def logout(
    current_user: Customer = Depends(get_current_user)
):
    """
    Logout the current user.
    
    In a production environment, this would invalidate the token.
    For now, it just returns a success response.
    """
    return {
        "success": True,
        "message": "Logged out successfully"
    }