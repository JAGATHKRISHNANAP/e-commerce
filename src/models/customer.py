# src/models/customer.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    customer_email = Column(String(255), unique=True, nullable=False, index=True)
    # Nullable while SMS is dormant; stays unique so SMS can be re-enabled later
    # without a schema change.
    customer_ph_no = Column(String(20), unique=True, nullable=True, index=True)
    customer_name = Column(String(255), nullable=True)  # Nullable for initial registration
    # Bcrypt hash. Nullable so legacy OTP-only accounts (pre-password-migration)
    # can finish the forgot-password flow before they have a hash.
    password_hash = Column(String(255), nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    date_of_registration = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships (for future use)
    # orders = relationship("Order", back_populates="customer")
    # cart_items = relationship("CartItem", back_populates="customer")
    cart = relationship("Cart", back_populates="customer", uselist=False)

    addresses = relationship("CustomerAddress", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer")

# Create indexes
Index('idx_customers_email', Customer.customer_email)
Index('idx_customers_phone', Customer.customer_ph_no)