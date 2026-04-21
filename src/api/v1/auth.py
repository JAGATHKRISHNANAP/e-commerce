# src/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional, Union
from config.database import get_db
from src.schemas.auth import (
    SendOTPRequest, SendOTPResponse,
    VerifyOTPRequest, AuthResponse,
    RegisterRequest, LoginRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    PendingVerificationResponse, GenericSuccessResponse,
    CompleteRegistrationRequest,
    UpdateProfileRequest, ChangePasswordRequest,
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

        payload = AuthService.verify_token(token)
        customer_id = payload.get("sub")

        if not customer_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"}
            )

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


# --------------------------------------------------------------- Register

@router.post("/auth/register", response_model=SendOTPResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new customer with email + password + name. The account starts
    `email_verified=false`. A verification OTP is dispatched to the email and
    must be confirmed via /auth/verify-email before a JWT is issued.
    """
    return AuthService.register(request, db)


# --------------------------------------------------------------- Login

@router.post(
    "/auth/login",
    response_model=Union[AuthResponse, PendingVerificationResponse],
)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Email + password login. If the password matches but email is unverified,
    returns `{ pending_verification: true, email }` and dispatches a fresh
    verification code; the frontend should route to the verify-email step.
    """
    return AuthService.login(request, db)


# ------------------------------------------------------- Email verification

@router.post("/auth/verify-email", response_model=AuthResponse)
async def verify_email(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Confirm a verification OTP. Flips `email_verified` to true and issues
    JWT + refresh token. Used both right after register and after a login
    that returned `pending_verification: true`.
    """
    return AuthService.verify_email(request, db)


@router.post("/auth/resend-verification", response_model=SendOTPResponse)
async def resend_verification(
    request: SendOTPRequest, db: Session = Depends(get_db)
):
    """Resend a verification OTP for an unverified account."""
    return AuthService.resend_verification_otp(request, db)


# ------------------------------------------------------- Forgot / Reset

@router.post("/auth/forgot-password", response_model=GenericSuccessResponse)
async def forgot_password(
    request: ForgotPasswordRequest, db: Session = Depends(get_db)
):
    """
    Send a password-reset OTP to the email if an account exists. Always
    returns success — does not reveal whether the email is registered.
    """
    return AuthService.forgot_password(request, db)


@router.post("/auth/reset-password", response_model=AuthResponse)
async def reset_password(
    request: ResetPasswordRequest, db: Session = Depends(get_db)
):
    """
    Confirm the reset OTP and set a new password. Issues a fresh JWT so the
    user is signed in immediately after reset. Also flips email_verified=true
    so legacy OTP-only accounts (no password yet) finish the migration here.
    """
    return AuthService.reset_password(request, db)


# ---------------------------------------------------------- Profile

@router.get("/auth/me")
async def get_current_user_info(
    current_user: Customer = Depends(get_current_user)
):
    return {
        "customer_id": current_user.customer_id,
        "email": current_user.customer_email,
        "phone_number": current_user.customer_ph_no,
        "name": current_user.customer_name,
        "is_verified": bool(current_user.email_verified),
        "email_verified": bool(current_user.email_verified),
        "created_at": current_user.date_of_registration.isoformat(),
        "is_profile_complete": current_user.customer_name is not None,
    }


@router.patch("/auth/me")
async def update_profile(
    request: UpdateProfileRequest,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the authenticated customer's name and/or phone number.
    Email is not editable here (requires re-verification)."""
    return AuthService.update_profile(request, current_user, db)


@router.post("/auth/change-password", response_model=GenericSuccessResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the authenticated user's password. Requires current password."""
    return AuthService.change_password(request, current_user, db)


@router.post("/auth/logout")
async def logout(current_user: Customer = Depends(get_current_user)):
    """Stateless JWT — frontend just discards the token. Endpoint kept so
    existing clients that POST here keep working."""
    return {"success": True, "message": "Logged out successfully"}


# ---------------------------------------------------------- Legacy

@router.post("/auth/complete-registration")
async def complete_registration(
    request: CompleteRegistrationRequest,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Legacy endpoint kept for older frontend builds. New flow collects
    name during /auth/register so this is a no-op for newly created users."""
    return AuthService.complete_registration(
        request,
        current_user.customer_id,
        db
    )
