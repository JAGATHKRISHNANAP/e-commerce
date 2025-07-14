# # src/services/auth_service.py
# from datetime import datetime, timedelta
# from typing import Optional, Dict, Any
# import secrets
# import jwt
# from sqlalchemy.orm import Session
# from fastapi import HTTPException, status,UploadFile
# from src.models.vendor import Vendor as Customer
# from src.models.otp import OTP
# from src.schemas.vendor_auth import (
#     SendOTPRequest, SendOTPResponse, 
#     VerifyOTPRequest, AuthResponse,
#     CompleteRegistrationRequest
# )
# import hashlib
# import os
# import traceback

# # JWT settings (move to config in production)
# SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_HOURS = 24

# class AuthVendorService:
    
#     @staticmethod
#     def send_otp(request: SendOTPRequest, db: Session) -> SendOTPResponse:
#         """Send OTP to phone number"""
#         try:
#             # For testing, always use static OTP
#             otp_code = "123456"
            
#             # Invalidate any existing OTPs for this phone number
#             db.query(OTP).filter(
#                 OTP.phone_number == request.phone_number,
#                 OTP.is_used == False
#             ).update({"is_used": True})
            
#             # Create new OTP record
#             otp_record = OTP(
#                 phone_number=request.phone_number,
#                 otp_code=otp_code,
#                 expires_at=datetime.utcnow() + timedelta(minutes=10)
#             )
#             db.add(otp_record)
#             db.commit()
            
#             # Generate OTP ID (hash of phone + timestamp)
#             otp_id = hashlib.md5(
#                 f"{request.phone_number}{datetime.utcnow()}".encode()
#             ).hexdigest()
            
#             # In production, send SMS here
#             # sms_service.send_otp(request.phone_number, otp_code)
            
#             return SendOTPResponse(
#                 success=True,
#                 message="OTP sent successfully",
#                 otp_id=otp_id,
#                 expires_in=600
#             )
            
#         except Exception as e:
#             db.rollback()
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to send OTP: {str(e)}"
#             )
    
#     @staticmethod
#     def verify_otp(request: VerifyOTPRequest, db: Session) -> AuthResponse:
#         """Verify OTP and authenticate/register user"""
#         try:
#             # Find valid OTP
#             otp_record = db.query(OTP).filter(
#                 OTP.phone_number == request.phone_number,
#                 OTP.otp_code == request.otp,
#                 OTP.is_used == False,
#                 OTP.expires_at > datetime.utcnow()
#             ).first()
            
#             if not otp_record:
#                 # Check if OTP exists but is expired or used
#                 expired_otp = db.query(OTP).filter(
#                     OTP.phone_number == request.phone_number,
#                     OTP.otp_code == request.otp
#                 ).first()
                
#                 if expired_otp:
#                     if expired_otp.is_used:
#                         raise HTTPException(
#                             status_code=status.HTTP_400_BAD_REQUEST,
#                             detail="This OTP has already been used"
#                         )
#                     else:
#                         raise HTTPException(
#                             status_code=status.HTTP_400_BAD_REQUEST,
#                             detail="OTP has expired. Please request a new one"
#                         )
#                 else:
#                     # Increment attempts
#                     db.query(OTP).filter(
#                         OTP.phone_number == request.phone_number,
#                         OTP.is_used == False
#                     ).update({"attempts": OTP.attempts + 1})
#                     db.commit()
                    
#                     raise HTTPException(
#                         status_code=status.HTTP_400_BAD_REQUEST,
#                         detail="Invalid OTP. Please check and try again"
#                     )
            
#             # Mark OTP as used
#             otp_record.is_used = True
#             db.commit()
            
#             # Check if customer exists
#             customer = db.query(Customer).filter(
#                 Customer.vendor_ph_no == request.phone_number
#             ).first()
            
#             is_new_user = False
#             if not customer:
#                 # Create new customer with just phone number
#                 customer = Customer(
#                     vendor_ph_no=request.phone_number,
#                     vendor_name=None  # Name will be added later
#                 )
#                 db.add(customer)
#                 db.commit()
#                 db.refresh(customer)
#                 is_new_user = True
            
#             # Generate JWT token
#             access_token = AuthVendorService.create_access_token(
#                 data={"sub": str(customer.vendor_id), "phone": customer.vendor_ph_no}
#             )
            
#             # Prepare user data
#             user_data = {
#                 # "vendor_id": customer.vendor_id,
#                 # "phone_number": customer.vendor_ph_no,
#                 # "name": customer.vendor_name,
#                 # "is_verified": True,
#                 # "created_at": customer.date_of_registration.isoformat(),
#                 # "is_profile_complete": customer.vendor_name is not None

#                     "vendor_id": customer.vendor_id,
#                     "phone_number": customer.vendor_ph_no,
#                     "name": customer.vendor_name,
#                     "email": customer.vendor_email,
#                     "aadhar_number": customer.aadhar_number,
#                     # "personal_address": customer.personal_address,
#                     "business_name": customer.business_name,
#                     "business_type": customer.business_type,
#                     "gst_number": customer.gst_number,
#                     "business_address": customer.business_address,
#                     "account_holder_name": customer.account_holder_name,
#                     "account_number": customer.account_number,
#                     "ifsc_code": customer.ifsc_code,
#                     "vendor_photo_path": customer.vendor_photo_path,
#                     "is_verified": True,
#                     "is_profile_complete": customer.vendor_name is not None,
#                     "created_at": customer.date_of_registration.isoformat()

#             }
            
#             return AuthResponse(
#                 success=True,
#                 token=access_token,
#                 refresh_token=AuthVendorService.create_refresh_token(
#                     data={"sub": str(customer.vendor_id)}
#                 ),
#                 user=user_data,
#                 expires_at=datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
#                 is_new_user=is_new_user
#             )
            
#         except HTTPException:
#             raise
#         except Exception as e:
#             db.rollback()
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to verify OTP: {str(e)}"
#             )
    
    

#     @staticmethod
#     def complete_registration(data: dict, vendor_id: int, db: Session, vendor_photo: Optional[UploadFile]) -> Dict[str, Any]:
#         from pathlib import Path
#         import shutil
#         import traceback  # Make sure this is imported

#         try:
#             customer = db.query(Customer).filter(Customer.vendor_id == vendor_id).first()

#             if not customer:
#                 raise HTTPException(status_code=404, detail="Customer not found")

#             if customer.vendor_ph_no != data["phone_number"]:
#                 raise HTTPException(status_code=400, detail="Phone number mismatch")

#             # Update fields
#             customer.vendor_name = data["name"]
#             customer.vendor_email = data.get("email")
#             customer.aadhar_number = data["aadhar_number"]

#             # Updated Address Fields
#             customer.address_line1 = data["address_line1"]
#             customer.address_line2 = data.get("address_line2", "")
#             customer.district = data["district"]
#             customer.state = data["state"]
#             customer.pincode = data["pincode"]

#             customer.business_name = data["business_name"]
#             customer.business_type = data["business_type"]
#             customer.gst_number = data.get("gst_number")
#             customer.business_address = data["business_address"]
#             customer.account_holder_name = data["account_holder_name"]
#             customer.account_number = data["account_number"]
#             customer.ifsc_code = data["ifsc_code"]

#             # Save vendor photo
#             if vendor_photo:
#                 vendor_dir = Path(f"media/vendor_photos/{vendor_id}")
#                 vendor_dir.mkdir(parents=True, exist_ok=True)

#                 file_path = vendor_dir / vendor_photo.filename.replace(" ", "_")
#                 with open(file_path, "wb") as buffer:
#                     shutil.copyfileobj(vendor_photo.file, buffer)

#                 customer.vendor_photo_path = str(file_path)

#             db.commit()
#             db.refresh(customer)

#             return {
#                 "success": True,
#                 "message": "Registration completed successfully",
#                 "user": {
#                     "vendor_id": customer.vendor_id,
#                     "phone_number": customer.vendor_ph_no,
#                     "name": customer.vendor_name,
#                     "email": customer.vendor_email,
#                     "is_verified": True,
#                     "created_at": customer.date_of_registration.isoformat(),
#                     "photo_url": customer.vendor_photo_path,
#                     "is_profile_complete": True
#                 }
#             }

#         except Exception as e:
#             db.rollback()
#             traceback.print_exc()
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Failed to complete registration: {str(e)}"
#             )


    
#     @staticmethod
#     def create_access_token(data: dict) -> str:
#         """Create JWT access token"""
#         to_encode = data.copy()
#         expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
#         to_encode.update({"exp": expire})
#         encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#         return encoded_jwt
    
#     @staticmethod
#     def create_refresh_token(data: dict) -> str:
#         """Create JWT refresh token"""
#         to_encode = data.copy()
#         expire = datetime.utcnow() + timedelta(days=30)
#         to_encode.update({"exp": expire, "type": "refresh"})
#         encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#         return encoded_jwt
    
#     @staticmethod
#     def verify_token(token: str) -> dict:
#         """Verify JWT token"""
#         try:
#             payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#             return payload
#         except jwt.ExpiredSignatureError:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Token has expired"
#             )
#         except jwt.JWTError:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid token"
#             )







# src/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from src.models.vendor import Vendor as Customer
from src.models.otp import OTP
from src.schemas.vendor_auth import (
    SendOTPRequest, SendOTPResponse, 
    VerifyOTPRequest, AuthResponse,
    CompleteRegistrationRequest
)
import hashlib
import os
import traceback

# JWT settings (move to config in production)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

class AuthVendorService:
    
    @staticmethod
    def send_otp(request: SendOTPRequest, db: Session) -> SendOTPResponse:
        """Send OTP to phone number"""
        try:
            # For testing, always use static OTP
            otp_code = "123456"
            
            # Invalidate any existing OTPs for this phone number
            db.query(OTP).filter(
                OTP.phone_number == request.phone_number,
                OTP.is_used == False
            ).update({"is_used": True})
            
            # Create new OTP record
            otp_record = OTP(
                phone_number=request.phone_number,
                otp_code=otp_code,
                expires_at=datetime.utcnow() + timedelta(minutes=10)
            )
            db.add(otp_record)
            db.commit()
            
            # Generate OTP ID (hash of phone + timestamp)
            otp_id = hashlib.md5(
                f"{request.phone_number}{datetime.utcnow()}".encode()
            ).hexdigest()
            
            # In production, send SMS here
            # sms_service.send_otp(request.phone_number, otp_code)
            
            return SendOTPResponse(
                success=True,
                message="OTP sent successfully",
                otp_id=otp_id,
                expires_in=600
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send OTP: {str(e)}"
            )
    
    @staticmethod
    def verify_otp(request: VerifyOTPRequest, db: Session) -> AuthResponse:
        """Verify OTP and authenticate/register user"""
        try:
            # Find valid OTP
            otp_record = db.query(OTP).filter(
                OTP.phone_number == request.phone_number,
                OTP.otp_code == request.otp,
                OTP.is_used == False,
                OTP.expires_at > datetime.utcnow()
            ).first()
            
            if not otp_record:
                # Check if OTP exists but is expired or used
                expired_otp = db.query(OTP).filter(
                    OTP.phone_number == request.phone_number,
                    OTP.otp_code == request.otp
                ).first()
                
                if expired_otp:
                    if expired_otp.is_used:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="This OTP has already been used"
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="OTP has expired. Please request a new one"
                        )
                else:
                    # Increment attempts
                    db.query(OTP).filter(
                        OTP.phone_number == request.phone_number,
                        OTP.is_used == False
                    ).update({"attempts": OTP.attempts + 1})
                    db.commit()
                    
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid OTP. Please check and try again"
                    )
            
            # Mark OTP as used
            otp_record.is_used = True
            db.commit()
            
            # Check if customer exists
            customer = db.query(Customer).filter(
                Customer.vendor_ph_no == request.phone_number
            ).first()
            
            is_new_user = False
            if not customer:
                # Create new customer with just phone number
                customer = Customer(
                    vendor_ph_no=request.phone_number,
                    vendor_name=None  # Name will be added later
                )
                db.add(customer)
                db.commit()
                db.refresh(customer)
                is_new_user = True
            
            # Generate JWT token - FIXED: Convert vendor_id to string consistently
            access_token = AuthVendorService.create_access_token(
                data={
                    "sub": str(customer.vendor_id),  # Always string
                    "phone": customer.vendor_ph_no,
                    "vendor_id": customer.vendor_id  # Keep as int for backwards compatibility
                }
            )
            
            # Prepare user data
            user_data = {
                "vendor_id": customer.vendor_id,
                "phone_number": customer.vendor_ph_no,
                "name": customer.vendor_name,
                "email": customer.vendor_email,
                "aadhar_number": customer.aadhar_number,
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
                "created_at": customer.date_of_registration.isoformat() if customer.date_of_registration else None
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
            traceback.print_exc()  # Add for debugging
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify OTP: {str(e)}"
            )
    
    @staticmethod
    def complete_registration(data: dict, vendor_id: int, db: Session, vendor_photo: Optional[UploadFile]) -> Dict[str, Any]:
        from pathlib import Path
        import shutil
        import traceback

        try:
            customer = db.query(Customer).filter(Customer.vendor_id == vendor_id).first()

            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")

            if customer.vendor_ph_no != data["phone_number"]:
                raise HTTPException(status_code=400, detail="Phone number mismatch")

            # Update fields
            customer.vendor_name = data["name"]
            customer.vendor_email = data.get("email")
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
                    "created_at": customer.date_of_registration.isoformat() if customer.date_of_registration else None,
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

    @staticmethod
    def create_access_token(data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})  # Add issued at time
        
        # Debug: Print token data
        print(f"Creating token with data: {to_encode}")
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        # Debug: Print generated token
        print(f"Generated token: {encoded_jwt}")
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=30)
        to_encode.update({"exp": expire, "type": "refresh", "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify JWT token"""
        try:
            # Debug: Print token being verified
            print(f"Verifying token: {token}")
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Debug: Print decoded payload
            print(f"Decoded payload: {payload}")
            
            return payload
        except jwt.ExpiredSignatureError as e:
            print(f"Token expired: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            print(f"Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}"
            )