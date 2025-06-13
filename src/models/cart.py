# src/models/cart.py
from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class Cart(Base):
    __tablename__ = "carts"
    
    cart_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="cart")
    cart_items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    
    # Create unique constraint - one cart per customer
    __table_args__ = (
        UniqueConstraint('customer_id', name='unique_customer_cart'),
    )

class CartItem(Base):
    __tablename__ = "cart_items"
    
    cart_item_id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.cart_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    added_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Price at the time of adding to cart (to handle price changes)
    price_at_time = Column(DECIMAL(10, 2), nullable=False)
    
    # Relationships
    cart = relationship("Cart", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")
    
    # Unique constraint - one product per cart
    __table_args__ = (
        UniqueConstraint('cart_id', 'product_id', name='unique_cart_product'),
    )

# Create indexes
Index('idx_carts_customer_id', Cart.customer_id)
Index('idx_cart_items_cart_id', CartItem.cart_id)
Index('idx_cart_items_product_id', CartItem.product_id)