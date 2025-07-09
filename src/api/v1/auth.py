# src/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from config.database import get_db
from src.schemas.auth import (
    SendOTPRequest, SendOTPResponse,
    VerifyOTPRequest, AuthResponse,
    CompleteRegistrationRequest
)
from src.services.auth_service import AuthService
from src.models.customer import Customer

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
        payload = AuthService.verify_token(token)
        customer_id = payload.get("sub")
        
        if not customer_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get customer from database
        customer = db.query(Customer).filter(
            Customer.customer_id == int(customer_id)
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
    return AuthService.send_otp(request, db)

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
    return AuthService.verify_otp(request, db)

@router.post("/auth/complete-registration")
async def complete_registration(
    request: CompleteRegistrationRequest,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete registration by adding the customer's name.
    
    This endpoint is called after OTP verification for new users.
    Requires authentication token from verify-otp response.
    """
    return AuthService.complete_registration(
        request, 
        current_user.customer_id, 
        db
    )

@router.get("/auth/me")
async def get_current_user_info(
    current_user: Customer = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Requires valid JWT token in Authorization header.
    """
    return {
        "customer_id": current_user.customer_id,
        "phone_number": current_user.customer_ph_no,
        "name": current_user.customer_name,
        "is_verified": True,
        "created_at": current_user.date_of_registration.isoformat(),
        "is_profile_complete": current_user.customer_name is not None
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