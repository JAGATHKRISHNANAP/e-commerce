
# src/models/address.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models import Base

class CustomerAddress(Base):
    __tablename__ = "customer_addresses"
    
    address_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    address_type = Column(String(20), nullable=False)  # 'home', 'office'
    full_name = Column(String(100), nullable=False)
    phone_number = Column(String(15), nullable=False)
    pincode = Column(String(6), nullable=False)
    address_line1 = Column(Text, nullable=False)
    address_line2 = Column(Text, nullable=True)
    landmark = Column(String(100), nullable=True)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="addresses")
    orders = relationship("Order", back_populates="delivery_address")
