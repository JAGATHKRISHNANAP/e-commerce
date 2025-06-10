# src/models/product.py
from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, Index
from sqlalchemy.orm import relationship
from config.database import Base

class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    stock_quantity = Column(Integer, default=0)
    image_url = Column(Text)
    storage_capacity = Column(String(50))
    
    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")

# Create indexes
Index('idx_products_category_id', Product.category_id)
Index('idx_products_name', Product.name)



