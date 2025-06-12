# src/models/otp.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime, timedelta
from config.database import Base

class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))
    is_used = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)