# src/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status,UploadFile
from src.models.vendor import Vendor as Customer
from src.models.otp import OTP
from src.schemas.vendor_auth import (
    SendOTPRequest, SendOTPResponse,
    VerifyOTPRequest, AuthResponse,
    CompleteRegistrationRequest
)
from src.services.otp_service import (
    OTPDeliveryError,
    OTP_EXPIRY_MINUTES,
    OTP_MAX_ATTEMPTS,
    OTP_RESEND_COOLDOWN_SECONDS,
    deliver_otp,
    generate_otp,
)
import hashlib
import logging
import os
import traceback

logger = logging.getLogger(__name__)

# JWT settings (move to config in production)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

class AuthVendorService:
    
    @staticmethod
    def send_otp(request: SendOTPRequest, db: Session) -> SendOTPResponse:
        """Generate a fresh OTP, persist it, and dispatch via the configured provider."""
        email = request.email.lower()
        try:
            now = datetime.utcnow()

            cooldown_cutoff = now - timedelta(seconds=OTP_RESEND_COOLDOWN_SECONDS)
            recent = db.query(OTP).filter(
                OTP.identifier == email,
                OTP.created_at > cooldown_cutoff,
            ).order_by(OTP.created_at.desc()).first()
            if recent:
                wait = OTP_RESEND_COOLDOWN_SECONDS - int((now - recent.created_at).total_seconds())
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Please wait {max(wait, 1)} seconds before requesting another OTP",
                )

            otp_code = generate_otp()

            db.query(OTP).filter(
                OTP.identifier == email,
                OTP.is_used == False
            ).update({"is_used": True})

            expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)
            otp_record = OTP(
                identifier=email,
                otp_code=otp_code,
                expires_at=expires_at,
            )
            db.add(otp_record)
            db.commit()
            db.refresh(otp_record)

            try:
                deliver_otp(email, otp_code, purpose="vendor login")
            except OTPDeliveryError as delivery_error:
                otp_record.is_used = True
                db.commit()
                logger.error("Vendor OTP delivery failed: %s", delivery_error)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Unable to send OTP right now. Please try again shortly.",
                )

            otp_id = hashlib.md5(
                f"{email}{otp_record.id}{otp_record.created_at.isoformat()}".encode()
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
            logger.exception("Failed to send vendor OTP")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send OTP: {str(e)}"
            )

    @staticmethod
    def verify_otp(request: VerifyOTPRequest, db: Session) -> AuthResponse:
        """Verify OTP and authenticate/register user"""
        email = request.email.lower()
        try:
            active_otp = db.query(OTP).filter(
                OTP.identifier == email,
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

            if active_otp.otp_code != request.otp:
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

            otp_record = active_otp
            otp_record.is_used = True
            db.commit()

            customer = db.query(Customer).filter(
                Customer.vendor_email == email
            ).first()

            is_new_user = False
            if not customer:
                customer = Customer(
                    vendor_email=email,
                    vendor_name=None,  # Name will be added later
                )
                db.add(customer)
                db.commit()
                db.refresh(customer)
                is_new_user = True

            access_token = AuthVendorService.create_access_token(
                data={"sub": str(customer.vendor_id), "email": customer.vendor_email}
            )
            
            # Prepare user data
            user_data = {
                # "vendor_id": customer.vendor_id,
                # "phone_number": customer.vendor_ph_no,
                # "name": customer.vendor_name,
                # "is_verified": True,
                # "created_at": customer.date_of_registration.isoformat(),
                # "is_profile_complete": customer.vendor_name is not None

                    "vendor_id": customer.vendor_id,
                    "phone_number": customer.vendor_ph_no,
                    "name": customer.vendor_name,
                    "email": customer.vendor_email,
                    "aadhar_number": customer.aadhar_number,
                    # "personal_address": customer.personal_address,
                    "business_name": customer.business_name,
                    "business_type": customer.business_type,
                    "gst_number": customer.gst_number,
                    "business_address": customer.business_address,
                    "account_holder_name": customer.account_holder_name,
                    "account_number": customer.account_number,
                    "ifsc_code": customer.ifsc_code,
                    "vendor_photo_path": customer.vendor_photo_path,
                    "is_verified": True,
                    "is_profile_complete": customer.vendor_name is not None,
                    "created_at": customer.date_of_registration.isoformat()

            }
            
            return AuthResponse(
                success=True,
                token=access_token,
                refresh_token=AuthVendorService.create_refresh_token(
                    data={"sub": str(customer.vendor_id)}
                ),
                user=user_data,
                expires_at=datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
                is_new_user=is_new_user
            )
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify OTP: {str(e)}"
            )
    
    # @staticmethod
    # def complete_registration(
    #     request: CompleteRegistrationRequest, 
    #     vendor_id: int, 
    #     db: Session
    # ) -> Dict[str, Any]:
    #     """Complete registration by adding customer name"""
    #     try:
    #         customer = db.query(Customer).filter(
    #             Customer.vendor_id == vendor_id
    #         ).first()
            
    #         if not customer:
    #             raise HTTPException(
    #                 status_code=status.HTTP_404_NOT_FOUND,
    #                 detail="Customer not found"
    #             )
            
    #         if customer.vendor_ph_no != request.phone_number:
    #             raise HTTPException(
    #                 status_code=status.HTTP_400_BAD_REQUEST,
    #                 detail="Phone number mismatch"
    #             )
            
    #         # Update customer name
    #         customer.vendor_name = request.name
    #         db.commit()
    #         db.refresh(customer)
            
    #         return {
    #             "success": True,
    #             "message": "Registration completed successfully",
    #             "user": {
    #                 "vendor_id": customer.vendor_id,
    #                 "phone_number": customer.vendor_ph_no,
    #                 "name": customer.vendor_name,
    #                 "is_verified": True,
    #                 "created_at": customer.date_of_registration.isoformat(),
    #                 "is_profile_complete": True
    #             }
    #         }
            
    #     except HTTPException:
    #         raise
    #     except Exception as e:
    #         db.rollback()
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail=f"Failed to complete registration: {str(e)}"
    #         )


    @staticmethod
    def complete_registration(data: dict, vendor_id: int, db: Session, vendor_photo: Optional[UploadFile]) -> Dict[str, Any]:
        from pathlib import Path
        import shutil
        import traceback  # Make sure this is imported

        try:
            customer = db.query(Customer).filter(Customer.vendor_id == vendor_id).first()

            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")

            # Email is the login key; match on it. If the form submits a different
            # email we reject so users cannot retarget someone else's account.
            form_email = (data.get("email") or "").lower().strip()
            if form_email and customer.vendor_email != form_email:
                raise HTTPException(status_code=400, detail="Email mismatch")

            # Update fields
            customer.vendor_name = data["name"]
            # Phone is captured here during profile completion (was blank at login).
            customer.vendor_ph_no = data.get("phone_number") or customer.vendor_ph_no
            customer.aadhar_number = data["aadhar_number"]

            # Updated Address Fields
            customer.address_line1 = data["address_line1"]
            customer.address_line2 = data.get("address_line2", "")
            customer.district = data["district"]
            customer.state = data["state"]
            customer.pincode = data["pincode"]

            customer.business_name = data["business_name"]
            customer.business_type = data["business_type"]
            customer.gst_number = data.get("gst_number")
            customer.business_address = data["business_address"]
            customer.account_holder_name = data["account_holder_name"]
            customer.account_number = data["account_number"]
            customer.ifsc_code = data["ifsc_code"]

            # Save vendor photo
            if vendor_photo:
                vendor_dir = Path(f"media/vendor_photos/{vendor_id}")
                vendor_dir.mkdir(parents=True, exist_ok=True)

                file_path = vendor_dir / vendor_photo.filename.replace(" ", "_")
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(vendor_photo.file, buffer)

                customer.vendor_photo_path = str(file_path)

            db.commit()
            db.refresh(customer)

            return {
                "success": True,
                "message": "Registration completed successfully",
                "user": {
                    "vendor_id": customer.vendor_id,
                    "phone_number": customer.vendor_ph_no,
                    "name": customer.vendor_name,
                    "email": customer.vendor_email,
                    "is_verified": True,
                    "created_at": customer.date_of_registration.isoformat(),
                    "photo_url": customer.vendor_photo_path,
                    "is_profile_complete": True
                }
            }

        except Exception as e:
            db.rollback()
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to complete registration: {str(e)}"
            )

    # @staticmethod
    # def complete_registration(data: dict, vendor_id: int, db: Session, vendor_photo: Optional[UploadFile]) -> Dict[str, Any]:
    #     from pathlib import Path
    #     import shutil

    #     try:
    #         customer = db.query(Customer).filter(Customer.vendor_id == vendor_id).first()

    #         if not customer:
    #             raise HTTPException(status_code=404, detail="Customer not found")

    #         if customer.vendor_ph_no != data["phone_number"]:
    #             raise HTTPException(status_code=400, detail="Phone number mismatch")

    #         # Update fields
    #         customer.vendor_name = data["name"]
    #         customer.vendor_email = data.get("email")
    #         customer.aadhar_number = data["aadhar_number"]
    #         customer.personal_address = data["personal_address"]
    #         customer.business_name = data["business_name"]
    #         customer.business_type = data["business_type"]
    #         customer.gst_number = data.get("gst_number")
    #         customer.business_address = data["business_address"]
    #         customer.account_holder_name = data["account_holder_name"]
    #         customer.account_number = data["account_number"]
    #         customer.ifsc_code = data["ifsc_code"]

    #         # Save vendor photo
    #         if vendor_photo:
    #             vendor_dir = Path(f"media/vendor_photos/{vendor_id}")
    #             vendor_dir.mkdir(parents=True, exist_ok=True)

    #             file_path = vendor_dir / vendor_photo.filename.replace(" ", "_")
    #             with open(file_path, "wb") as buffer:
    #                 shutil.copyfileobj(vendor_photo.file, buffer)

    #             customer.vendor_photo_path = str(file_path)

    #         db.commit()
    #         db.refresh(customer)

    #         return {
    #             "success": True,
    #             "message": "Registration completed successfully",
    #             "user": {
    #                 "vendor_id": customer.vendor_id,
    #                 "phone_number": customer.vendor_ph_no,
    #                 "name": customer.vendor_name,
    #                 "email": customer.vendor_email,
    #                 "is_verified": True,
    #                 "created_at": customer.date_of_registration.isoformat(),
    #                 "photo_url": customer.vendor_photo_path,
    #                 "is_profile_complete": True
    #             }
    #         }

    #     except Exception as e:
    #         db.rollback()
    #         traceback.print_exc()  # Add this to print error details to the console
    #         raise HTTPException(
    #             status_code=500,
    #             detail=f"Failed to complete registration: {str(e)}"
    #         )


    
# @staticmethod
# def complete_registration(request: CompleteRegistrationRequest,data: dict, vendor_id: int, db: Session) -> Dict[str, Any]:
#     """Complete full vendor registration and persist all fields."""
#     try:
#         customer = db.query(Customer).filter(Customer.vendor_id == vendor_id).first()

#         if not customer:
#             raise HTTPException(status_code=404, detail="Customer not found")

#         if customer.vendor_ph_no != data["phone_number"]:
#             raise HTTPException(status_code=400, detail="Phone number mismatch")

#         # Update fields from form
#         customer.vendor_name = data["name"]
#         customer.vendor_email = data.get("email")
#         customer.aadhar_number = data["aadhar_number"]
#         customer.personal_address = data["personal_address"]
#         customer.business_name = data["business_name"]
#         customer.business_type = data["business_type"]
#         customer.gst_number = data.get("gst_number")
#         customer.business_address = data["business_address"]
#         customer.account_holder_name = data["account_holder_name"]
#         customer.account_number = data["account_number"]
#         customer.ifsc_code = data["ifsc_code"]

#         # Save profile photo if present
#         if data.get("vendor_photo"):
#             file = data["vendor_photo"]
#             filename = f"{customer.vendor_id}_{file.filename.replace(' ', '_')}"
#             file_path = f"media/vendor_photos/{filename}"

#             # Ensure directory exists
#             os.makedirs(os.path.dirname(file_path), exist_ok=True)

#             with open(file_path, "wb") as f:
#                 f.write(file.file.read())

#             customer.vendor_photo_path = file_path

#         db.commit()
#         db.refresh(customer)

#         return {
#             "success": True,
#             "message": "Registration completed successfully",
#             "user": {
#                 "vendor_id": customer.vendor_id,
#                 "phone_number": customer.vendor_ph_no,
#                 "name": customer.vendor_name,
#                 "email": customer.vendor_email,
#                 "is_verified": True,
#                 "is_profile_complete": True,
#                 "created_at": customer.date_of_registration.isoformat(),
#                 "photo_url": customer.vendor_photo_path  # or construct full URL
#             }
#         }

#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to complete registration: {str(e)}"
#         )










    
    @staticmethod
    def create_access_token(data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=30)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )