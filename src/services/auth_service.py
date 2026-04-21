# src/services/auth_service.py
from datetime import datetime, timedelta
from typing import Dict, Any, Union
import hashlib
import logging
import os

import bcrypt
import jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.models.customer import Customer
from src.models.otp import (
    OTP,
    OTP_PURPOSE_VERIFY_EMAIL,
    OTP_PURPOSE_RESET_PASSWORD,
)
from src.schemas.auth import (
    SendOTPRequest, SendOTPResponse,
    VerifyOTPRequest, AuthResponse,
    RegisterRequest, LoginRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    PendingVerificationResponse,
    GenericSuccessResponse,
    CompleteRegistrationRequest,
    UpdateProfileRequest, ChangePasswordRequest,
)
from src.services.otp_service import (
    OTPDeliveryError,
    OTP_EXPIRY_MINUTES,
    OTP_MAX_ATTEMPTS,
    OTP_RESEND_COOLDOWN_SECONDS,
    deliver_otp,
    generate_otp,
)

logger = logging.getLogger(__name__)

# JWT settings (move to config in production)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# bcrypt has a hard 72-byte input limit; clip to keep silent truncation from
# producing different hashes on different inputs.
def _prep(password: str) -> bytes:
    return password.encode("utf-8")[:72]


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(_prep(password), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(_prep(password), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _user_payload(customer: Customer) -> Dict[str, Any]:
    return {
        "customer_id": customer.customer_id,
        "email": customer.customer_email,
        "phone_number": customer.customer_ph_no,
        "name": customer.customer_name,
        "is_verified": bool(customer.email_verified),
        "email_verified": bool(customer.email_verified),
        "created_at": customer.date_of_registration.isoformat(),
        "is_profile_complete": customer.customer_name is not None,
    }


class AuthService:

    # ------------------------------------------------------------------ OTP

    @staticmethod
    def _issue_otp(
        db: Session,
        email: str,
        purpose: str,
        delivery_label: str,
    ) -> SendOTPResponse:
        """Generate, persist, and send a fresh OTP scoped to (email, purpose)."""
        try:
            now = datetime.utcnow()

            cooldown_cutoff = now - timedelta(seconds=OTP_RESEND_COOLDOWN_SECONDS)
            recent = db.query(OTP).filter(
                OTP.identifier == email,
                OTP.purpose == purpose,
                OTP.created_at > cooldown_cutoff,
            ).order_by(OTP.created_at.desc()).first()
            if recent:
                wait = OTP_RESEND_COOLDOWN_SECONDS - int((now - recent.created_at).total_seconds())
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Please wait {max(wait, 1)} seconds before requesting another OTP",
                )

            otp_code = generate_otp()

            # Invalidate older unused codes for the SAME purpose so a fresh send
            # supersedes the previous one — codes for other purposes are left
            # alone (a verify_email code shouldn't clobber a reset_password code).
            db.query(OTP).filter(
                OTP.identifier == email,
                OTP.purpose == purpose,
                OTP.is_used == False
            ).update({"is_used": True})

            expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)
            otp_record = OTP(
                identifier=email,
                otp_code=otp_code,
                purpose=purpose,
                expires_at=expires_at,
            )
            db.add(otp_record)
            db.commit()
            db.refresh(otp_record)

            try:
                deliver_otp(email, otp_code, purpose=delivery_label)
            except OTPDeliveryError as delivery_error:
                otp_record.is_used = True
                db.commit()
                logger.error("Customer OTP delivery failed: %s", delivery_error)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Unable to send OTP right now. Please try again shortly.",
                )

            otp_id = hashlib.md5(
                f"{email}{purpose}{otp_record.id}{otp_record.created_at.isoformat()}".encode()
            ).hexdigest()

            return SendOTPResponse(
                success=True,
                message="OTP sent successfully",
                otp_id=otp_id,
                expires_in=OTP_EXPIRY_MINUTES * 60,
            )

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.exception("Failed to send customer OTP")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send OTP: {str(e)}"
            )

    @staticmethod
    def _consume_otp(db: Session, email: str, code: str, purpose: str) -> None:
        """Validate `code` against the latest unused OTP scoped to (email, purpose).

        Raises HTTPException on any failure; marks the row used on success.
        """
        active_otp = db.query(OTP).filter(
            OTP.identifier == email,
            OTP.purpose == purpose,
            OTP.is_used == False,
        ).order_by(OTP.created_at.desc()).first()

        if not active_otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active OTP found. Please request a new one.",
            )

        if active_otp.expires_at <= datetime.utcnow():
            active_otp.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired. Please request a new one",
            )

        if active_otp.attempts >= OTP_MAX_ATTEMPTS:
            active_otp.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many invalid attempts. Please request a new OTP.",
            )

        if active_otp.otp_code != code:
            active_otp.attempts = (active_otp.attempts or 0) + 1
            remaining = max(OTP_MAX_ATTEMPTS - active_otp.attempts, 0)
            if remaining == 0:
                active_otp.is_used = True
            db.commit()
            if remaining == 0:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many invalid attempts. Please request a new OTP.",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid OTP. {remaining} attempt(s) remaining.",
            )

        active_otp.is_used = True
        db.commit()

    # ----------------------------------------------------------- Register

    @staticmethod
    def register(request: RegisterRequest, db: Session) -> SendOTPResponse:
        """Create the customer (email_verified=false) and dispatch a verification OTP.

        Returning a verification OTP rather than a JWT keeps unverified emails
        from holding a live session.
        """
        email = request.email.lower()
        existing = db.query(Customer).filter(Customer.customer_email == email).first()

        if existing and existing.password_hash and existing.email_verified:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account already exists for this email. Please log in instead.",
            )

        try:
            if existing:
                # Two cases land here:
                #  - user registered earlier but never verified — refresh details
                #  - legacy OTP-only user (email_verified=true, no password)
                #    chose to "register again" — we let them set a password and
                #    re-verify via the OTP flow.
                existing.password_hash = _hash_password(request.password)
                existing.customer_name = request.name
                existing.email_verified = False
                customer = existing
            else:
                customer = Customer(
                    customer_email=email,
                    customer_name=request.name,
                    password_hash=_hash_password(request.password),
                    email_verified=False,
                )
                db.add(customer)
            db.commit()
            db.refresh(customer)
        except HTTPException:
            raise
        except Exception:
            db.rollback()
            logger.exception("Failed to persist new customer during register")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create account",
            )

        return AuthService._issue_otp(
            db, email, OTP_PURPOSE_VERIFY_EMAIL, "customer email verification"
        )

    # ----------------------------------------------------------- Login

    @staticmethod
    def login(
        request: LoginRequest, db: Session
    ) -> Union[AuthResponse, PendingVerificationResponse]:
        email = request.email.lower()
        customer = db.query(Customer).filter(Customer.customer_email == email).first()

        if not customer or not customer.password_hash:
            # Either the email has no account, or it's a pre-migration row
            # without a password yet. Generic message either way (don't leak
            # which emails are registered).
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not _verify_password(request.password, customer.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not customer.email_verified:
            # Send a fresh verification code and tell the frontend to route
            # to the verify-email screen instead of issuing a token.
            AuthService._issue_otp(
                db, email, OTP_PURPOSE_VERIFY_EMAIL, "customer email verification"
            )
            return PendingVerificationResponse(email=email)

        return AuthService._build_auth_response(customer, is_new_user=False)

    # ----------------------------------------------- Email verification (post-register or post-login)

    @staticmethod
    def verify_email(request: VerifyOTPRequest, db: Session) -> AuthResponse:
        email = request.email.lower()
        AuthService._consume_otp(db, email, request.otp, OTP_PURPOSE_VERIFY_EMAIL)

        customer = db.query(Customer).filter(Customer.customer_email == email).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found for this email. Please register first.",
            )

        was_unverified = not customer.email_verified
        customer.email_verified = True
        db.commit()
        db.refresh(customer)

        return AuthService._build_auth_response(customer, is_new_user=was_unverified)

    # --------------------------------------------- Forgot / Reset password

    @staticmethod
    def forgot_password(
        request: ForgotPasswordRequest, db: Session
    ) -> GenericSuccessResponse:
        """Always returns success (don't leak which emails are registered).
        Only actually sends a code if a customer exists."""
        email = request.email.lower()
        customer = db.query(Customer).filter(Customer.customer_email == email).first()
        if customer:
            try:
                AuthService._issue_otp(
                    db, email, OTP_PURPOSE_RESET_PASSWORD, "customer password reset"
                )
            except HTTPException as exc:
                # 429 cooldown is OK to surface; everything else is silent.
                if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    raise
                logger.warning("Forgot-password OTP failed for %s: %s", email, exc.detail)
        return GenericSuccessResponse(
            message="If an account exists for that email, a reset code has been sent.",
        )

    @staticmethod
    def reset_password(request: ResetPasswordRequest, db: Session) -> AuthResponse:
        email = request.email.lower()
        AuthService._consume_otp(db, email, request.otp, OTP_PURPOSE_RESET_PASSWORD)

        customer = db.query(Customer).filter(Customer.customer_email == email).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found for this email.",
            )

        customer.password_hash = _hash_password(request.new_password)
        # Resetting a password also clears any unverified state — completing
        # the OTP step is verification enough for legacy accounts.
        customer.email_verified = True
        db.commit()
        db.refresh(customer)

        return AuthService._build_auth_response(customer, is_new_user=False)

    # ---------------------------------------------------- Resend OTPs

    @staticmethod
    def resend_verification_otp(
        request: SendOTPRequest, db: Session
    ) -> SendOTPResponse:
        email = request.email.lower()
        customer = db.query(Customer).filter(Customer.customer_email == email).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found for this email. Please register first.",
            )
        if customer.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already verified. Please log in.",
            )
        return AuthService._issue_otp(
            db, email, OTP_PURPOSE_VERIFY_EMAIL, "customer email verification"
        )

    # ---------------------------------------------- Authenticated profile + password

    @staticmethod
    def update_profile(
        request: UpdateProfileRequest, customer: Customer, db: Session
    ) -> Dict[str, Any]:
        """Update name and/or phone on the authenticated customer. Unset
        fields are left untouched; sending phone_number="" clears it.
        """
        name = request.name
        phone = request.phone_number

        if name is None and phone is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one of name or phone_number must be provided",
            )

        if phone is not None and phone != (customer.customer_ph_no or None):
            clash = db.query(Customer).filter(
                Customer.customer_ph_no == phone,
                Customer.customer_id != customer.customer_id,
            ).first()
            if clash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This phone number is already in use by another account.",
                )
            customer.customer_ph_no = phone

        if name is not None:
            customer.customer_name = name

        db.commit()
        db.refresh(customer)
        return {
            "success": True,
            "message": "Profile updated",
            "user": _user_payload(customer),
        }

    @staticmethod
    def change_password(
        request: ChangePasswordRequest, customer: Customer, db: Session
    ) -> GenericSuccessResponse:
        if not customer.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No password is set for this account. Use forgot-password to create one.",
            )
        if not _verify_password(request.current_password, customer.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )
        if request.current_password == request.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from the current password",
            )
        customer.password_hash = _hash_password(request.new_password)
        db.commit()
        return GenericSuccessResponse(message="Password updated successfully")

    # ---------------------------------------------------- Legacy

    @staticmethod
    def complete_registration(
        request: CompleteRegistrationRequest,
        customer_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Legacy endpoint kept for older clients. Updates the customer name."""
        email = request.email.lower()
        customer = db.query(Customer).filter(
            Customer.customer_id == customer_id
        ).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )
        if customer.customer_email != email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email mismatch",
            )
        customer.customer_name = request.name
        db.commit()
        db.refresh(customer)
        return {
            "success": True,
            "message": "Registration completed successfully",
            "user": _user_payload(customer),
        }

    # ---------------------------------------------------- JWT helpers

    @staticmethod
    def _build_auth_response(
        customer: Customer, *, is_new_user: bool
    ) -> AuthResponse:
        access_token = AuthService.create_access_token(
            data={"sub": str(customer.customer_id), "email": customer.customer_email}
        )
        return AuthResponse(
            success=True,
            token=access_token,
            refresh_token=AuthService.create_refresh_token(
                data={"sub": str(customer.customer_id)}
            ),
            user=_user_payload(customer),
            expires_at=datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
            is_new_user=is_new_user,
        )

    @staticmethod
    def create_access_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=30)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    # ---------------------------------------------------- Removed

    # send_otp / verify_otp from the OTP-only era have been intentionally
    # removed. Use register / login / verify_email / forgot_password /
    # reset_password instead. The vendor service still has the old shape and
    # will be migrated in a follow-up pass.
