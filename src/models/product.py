# from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, Index
# from sqlalchemy.orm import relationship
# from config.database import Base

# class Product(Base):
#     __tablename__ = "products"
    
#     product_id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(255), nullable=False, index=True)
#     description = Column(Text)
#     price = Column(DECIMAL(10, 2), nullable=False)
#     category_id = Column(Integer, ForeignKey("categories.category_id"))
#     stock_quantity = Column(Integer, default=0)
#     image_url = Column(Text)
#     storage_capacity = Column(String(50))
    
#     category = relationship("Category", back_populates="products")
#     cart_items = relationship("CartItem", back_populates="product")

# # Create indexes
# Index('idx_products_category_id', Product.category_id)
# Index('idx_products_name', Product.name)





# src/models/product.py - Updated Product Model (without Category class)

from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    stock_quantity = Column(Integer, default=0)
    sku = Column(String(100), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional product attributes (optional)
    brand = Column(String(100))
    weight = Column(Numeric(8, 2))
    dimensions = Column(String(100))
    color = Column(String(50))
    size = Column(String(50))
    material = Column(String(100))
    
    # Relationships
    category = relationship("Category", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="product")

class ProductImage(Base):
    __tablename__ = "product_images"
    
    image_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="CASCADE"))
    image_url = Column(String(500), nullable=False)
    alt_text = Column(String(200))
    is_primary = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="images")