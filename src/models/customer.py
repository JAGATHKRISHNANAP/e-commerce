# src/models/customer.py
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class Customer(Base):
    __tablename__ = "customers"
    
    customer_id = Column(Integer, primary_key=True, index=True)
    customer_ph_no = Column(String(20), unique=True, nullable=False, index=True)
    customer_name = Column(String(255), nullable=True)  # Nullable for initial registration
    date_of_registration = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships (for future use)
    # orders = relationship("Order", back_populates="customer")
    # cart_items = relationship("CartItem", back_populates="customer")
    cart = relationship("Cart", back_populates="customer", uselist=False)

# Create indexes
Index('idx_customers_phone', Customer.customer_ph_no)