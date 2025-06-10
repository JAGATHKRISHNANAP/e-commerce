from sqlalchemy import Column, Integer, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class CartItem(Base):
    __tablename__ = "cart_items"
    
    cart_item_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity = Column(Integer, nullable=False, default=1)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

# Create indexes
Index('idx_cart_items_user_id', CartItem.user_id)
Index('idx_cart_items_product_id', CartItem.product_id)
