# # src/models/vendor.py
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class Vendor(Base):
    __tablename__ = "vendors"
    
    vendor_id = Column(Integer, primary_key=True, index=True)
    vendor_ph_no = Column(String(20), unique=True, nullable=False, index=True)
    vendor_name = Column(String(255), nullable=True)  # Nullable for initial registration
    date_of_registration = Column(DateTime, default=datetime.utcnow, nullable=False)
    vendor_email = Column(String, nullable=True)
    aadhar_number = Column(String(12), nullable=True)
    personal_address = Column(String, nullable=True)
    business_name = Column(String, nullable=True)
    business_type = Column(String, nullable=True)
    gst_number = Column(String, nullable=True)
    business_address = Column(String, nullable=True)
    account_holder_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)
    vendor_photo_path = Column(String, nullable=True)

        
    # Relationships (for future use)
    # orders = relationship("Order", back_populates="vendor")
    # cart_items = relationship("CartItem", back_populates="vendor")
    # cart = relationship("Cart", back_populates="vendor", uselist=False)

    # addresses = relationship("vendorAddress", back_populates="vendor", cascade="all, delete-orphan")
    # orders = relationship("Order", back_populates="vendor")

# Create indexes
# Index('idx_vendors_phone', vendor.vendor_ph_no)






































# from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum, Index, Numeric
# from sqlalchemy.orm import relationship
# from datetime import datetime
# from config.database import Base
# import enum

# class BusinessType(enum.Enum):
#     SOLE_PROPRIETORSHIP = "sole_proprietorship"
#     PARTNERSHIP = "partnership"
#     PRIVATE_LIMITED = "private_limited"
#     PUBLIC_LIMITED = "public_limited"
#     LLP = "llp"
#     ONE_PERSON_COMPANY = "one_person_company"
#     TRUST = "trust"
#     SOCIETY = "society"
#     COOPERATIVE = "cooperative"
#     OTHER = "other"

# class VendorStatus(enum.Enum):
#     PENDING = "pending"
#     UNDER_REVIEW = "under_review"
#     APPROVED = "approved"
#     REJECTED = "rejected"
#     SUSPENDED = "suspended"
#     INACTIVE = "inactive"

# class Vendor(Base):
#     __tablename__ = "vendors"
    
#     # Primary Information
#     vendor_id = Column(Integer, primary_key=True, index=True)
#     vendor_code = Column(String(20), unique=True, nullable=False, index=True)  # Auto-generated unique code
    
#     # Personal Information
#     owner_name = Column(String(255), nullable=False)
#     vendor_photo = Column(String(500), nullable=True)  # File path/URL for photo
#     phone_number = Column(String(20), unique=True, nullable=False, index=True)
#     email = Column(String(255), unique=True, nullable=False, index=True)
#     aadhar_number = Column(String(12), unique=True, nullable=False, index=True)
    
#     # Business Information
#     business_name = Column(String(255), nullable=False)
#     business_type = Column(Enum(BusinessType), nullable=False)
#     business_description = Column(Text, nullable=True)
#     gst_number = Column(String(15), unique=True, nullable=True, index=True)  # Optional
#     pan_number = Column(String(10), nullable=True)
    
#     # Address Information
#     address_line_1 = Column(String(255), nullable=False)
#     address_line_2 = Column(String(255), nullable=True)
#     city = Column(String(100), nullable=False)
#     state = Column(String(100), nullable=False)
#     postal_code = Column(String(10), nullable=False)
#     country = Column(String(100), default="India", nullable=False)
    
#     # Bank Information (for payments)
#     bank_name = Column(String(255), nullable=True)
#     account_number = Column(String(50), nullable=True)
#     ifsc_code = Column(String(11), nullable=True)
#     account_holder_name = Column(String(255), nullable=True)
    
#     # Business Details
#     years_in_business = Column(Integer, nullable=True)
#     # annual_turnover = Column(Numeric(15, 2), nullable=True)
#     # number_of_employees = Column(Integer, nullable=True)
    
#     # System Information
#     vendor_status = Column(Enum(VendorStatus), default=VendorStatus.PENDING, nullable=False)
#     registration_date = Column(DateTime, default=datetime.utcnow, nullable=False)
#     approval_date = Column(DateTime, nullable=True)
#     last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
#     # Verification flags
#     is_email_verified = Column(Boolean, default=False)
#     is_phone_verified = Column(Boolean, default=False)
#     is_documents_verified = Column(Boolean, default=False)
#     is_bank_verified = Column(Boolean, default=False)
    
#     # # Additional fields
#     # website_url = Column(String(255), unique=True, nullable=True, index=True)
#     # social_media_links = Column(Text,  unique=True, nullable=True, index=True)  # JSON string for multiple links
#     # business_license_number = Column(String(100),  unique=True, nullable=True, index=True)
#     # tax_registration_number = Column(String(50), unique=True, nullable=True, index=True)
    
#     # Terms and conditions
#     terms_accepted = Column(Boolean, default=False, nullable=False)
#     terms_accepted_date = Column(DateTime, nullable=True)
    
#     # Notes and remarks (for admin use)
#     admin_notes = Column(Text, nullable=True)
#     rejection_reason = Column(Text, nullable=True)
    
#     # Relationships (for future use)
#     # products = relationship("Product", back_populates="vendor")
#     # orders = relationship("Order", back_populates="vendor")
    
#     def __repr__(self):
#         return f"<Vendor(vendor_id={self.vendor_id}, business_name='{self.business_name}', status='{self.vendor_status}')>"

# # Create indexes for better performance
# Index('idx_vendors_phone', Vendor.phone_number)
# Index('idx_vendors_email', Vendor.email)
# Index('idx_vendors_gst', Vendor.gst_number)
# Index('idx_vendors_status', Vendor.vendor_status)
# Index('idx_vendors_code', Vendor.vendor_code)
# Index('idx_vendors_aadhar', Vendor.aadhar_number)