# src/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models.customer import Customer
from src.models.otp import OTP
from src.schemas.auth import (
    SendOTPRequest, SendOTPResponse, 
    VerifyOTPRequest, AuthResponse,
    CompleteRegistrationRequest
)
import hashlib
import os

# JWT settings (move to config in production)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

class AuthService:
    
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
                Customer.customer_ph_no == request.phone_number
            ).first()
            
            is_new_user = False
            if not customer:
                # Create new customer with just phone number
                customer = Customer(
                    customer_ph_no=request.phone_number,
                    customer_name=None  # Name will be added later
                )
                db.add(customer)
                db.commit()
                db.refresh(customer)
                is_new_user = True
            
            # Generate JWT token
            access_token = AuthService.create_access_token(
                data={"sub": str(customer.customer_id), "phone": customer.customer_ph_no}
            )
            
            # Prepare user data
            user_data = {
                "customer_id": customer.customer_id,
                "phone_number": customer.customer_ph_no,
                "name": customer.customer_name,
                "is_verified": True,
                "created_at": customer.date_of_registration.isoformat(),
                "is_profile_complete": customer.customer_name is not None
            }
            
            return AuthResponse(
                success=True,
                token=access_token,
                refresh_token=AuthService.create_refresh_token(
                    data={"sub": str(customer.customer_id)}
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
    
    @staticmethod
    def complete_registration(
        request: CompleteRegistrationRequest, 
        customer_id: int, 
        db: Session
    ) -> Dict[str, Any]:
        """Complete registration by adding customer name"""
        try:
            customer = db.query(Customer).filter(
                Customer.customer_id == customer_id
            ).first()
            
            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found"
                )
            
            if customer.customer_ph_no != request.phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number mismatch"
                )
            
            # Update customer name
            customer.customer_name = request.name
            db.commit()
            db.refresh(customer)
            
            return {
                "success": True,
                "message": "Registration completed successfully",
                "user": {
                    "customer_id": customer.customer_id,
                    "phone_number": customer.customer_ph_no,
                    "name": customer.customer_name,
                    "is_verified": True,
                    "created_at": customer.date_of_registration.isoformat(),
                    "is_profile_complete": True
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to complete registration: {str(e)}"
            )
    
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