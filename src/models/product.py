# # # src/models/product.py - Updated with primary image path
# # from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, Index
# # from sqlalchemy.orm import relationship
# # from config.database import Base

# # class Product(Base):
# #     __tablename__ = "products"
    
# #     product_id = Column(Integer, primary_key=True, index=True)
# #     name = Column(String(255), nullable=False, index=True)
# #     description = Column(Text)
# #     price = Column(DECIMAL(10, 2), nullable=False)
# #     category_id = Column(Integer, ForeignKey("categories.category_id"))
# #     stock_quantity = Column(Integer, default=0)
# #     storage_capacity = Column(String(50))
# #     created_by = Column(String(100), nullable=False)  # Sales user who created the product
    
# #     # Primary image fields for quick access
# #     primary_image_url = Column(String(500), nullable=True)  # URL of the primary image
# #     primary_image_filename = Column(String(255), nullable=True)  # Filename of primary image
    
# #     # Relationships
# #     category = relationship("Category", back_populates="products")
# #     cart_items = relationship("CartItem", back_populates="product")
# #     images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")

# # # Create indexes
# # Index('idx_products_category_id', Product.category_id)
# # Index('idx_products_name', Product.name)
# # Index('idx_products_created_by', Product.created_by)














# # src/models/product.py - Updated for dynamic specifications
# from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, Index, JSON, Boolean, DateTime
# from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func
# from config.database import Base

# class Product(Base):
#     __tablename__ = "products"
    
#     product_id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(255), nullable=False, index=True)
#     description = Column(Text)
#     category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
#     subcategory_id = Column(Integer, ForeignKey("subcategories.subcategory_id"), nullable=False)
    
#     # Dynamic specifications stored as JSON
#     specifications = Column(JSON, nullable=False, default={})  # {"ram": "8GB", "storage": "256GB", "color": "Black"}
    
#     # Pricing
#     base_price = Column(Integer, nullable=False)  # Base price in cents
#     calculated_price = Column(Integer, nullable=False)  # Final calculated price in cents
    
#     # Inventory
#     stock_quantity = Column(Integer, default=0)
#     sku = Column(String(100), unique=True, nullable=True, index=True)
    
#     # Metadata
#     created_by = Column(String(100), nullable=False)
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
#     # Image fields
#     primary_image_url = Column(String(500), nullable=True)
#     primary_image_filename = Column(String(255), nullable=True)
    
#     # Relationships
#     category = relationship("Category", back_populates="products")
#     subcategory = relationship("Subcategory", back_populates="products")
#     images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
#     cart_items = relationship("CartItem", back_populates="product")

# # Create indexes for better performance
# Index('idx_products_category_subcategory', Product.category_id, Product.subcategory_id)
# Index('idx_products_specifications', Product.specifications, postgresql_using='gin')
# Index('idx_products_active', Product.is_active)
# Index('idx_products_created_by', Product.created_by)



# src/models/product.py - Clean version without GIN index
from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Original pricing (keep for backward compatibility)
    price = Column(DECIMAL(10, 2), nullable=True)
    
    # New dynamic pricing
    base_price = Column(Integer, nullable=True)  # Base price in cents
    calculated_price = Column(Integer, nullable=True)  # Final calculated price in cents
    
    # Categories
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("subcategories.subcategory_id"), nullable=True)
    
    # Dynamic specifications - JSON column (NO GIN INDEX)
    specifications = Column(JSON, nullable=False, default={})
    
    # Inventory and metadata
    stock_quantity = Column(Integer, default=0)
    storage_capacity = Column(String(50))  # Keep for backward compatibility
    sku = Column(String(100), unique=True, nullable=True, index=True)
    created_by = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Image fields
    primary_image_url = Column(String(500), nullable=True)
    primary_image_filename = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="products")
    subcategory = relationship("Subcategory", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")

# NOTE: Regular indexes are created in the database setup script
# NO GIN indexes to avoid PostgreSQL issues