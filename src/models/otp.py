# src/models/otp.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime, timedelta
from config.database import Base

# OTP purposes — keeps a verify_email code from being replayed against a
# reset_password call (or vice versa).
OTP_PURPOSE_VERIFY_EMAIL = "verify_email"
OTP_PURPOSE_RESET_PASSWORD = "reset_password"

class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    # Channel-agnostic: holds an email today, a phone number when SMS returns.
    identifier = Column(String(255), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)
    purpose = Column(String(32), default=OTP_PURPOSE_VERIFY_EMAIL, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))
    is_used = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)