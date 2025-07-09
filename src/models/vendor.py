# # src/models/vendor.py
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id = Column(Integer, primary_key=True, index=True)
    vendor_ph_no = Column(String(20), unique=True, nullable=False, index=True)
    vendor_name = Column(String(255), nullable=True)
    date_of_registration = Column(DateTime, default=datetime.utcnow, nullable=False)
    vendor_email = Column(String, nullable=True)
    aadhar_number = Column(String(12), nullable=True)

    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, nullable=True)

    business_name = Column(String, nullable=True)
    business_type = Column(String, nullable=True)
    gst_number = Column(String, nullable=True)
    business_address = Column(String, nullable=True)

    account_holder_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)

    vendor_photo_path = Column(String, nullable=True)
