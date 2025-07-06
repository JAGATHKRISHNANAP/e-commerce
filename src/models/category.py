# # # src/models/category.py
# # from sqlalchemy import Column, Integer, String
# # from sqlalchemy.orm import relationship
# # from config.database import Base

# # class Category(Base):
# #     __tablename__ = "categories"
    
# #     category_id = Column(Integer, primary_key=True, index=True)
# #     name = Column(String(100), unique=True, nullable=False)
    
# #     products = relationship("Product", back_populates="category")







# # src/models/category.py - Enhanced for dynamic specifications
# from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
# from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func
# from config.database import Base

# class Category(Base):
#     __tablename__ = "categories"
    
#     category_id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(100), nullable=False, unique=True, index=True)
#     description = Column(Text, nullable=True)
#     is_active = Column(Boolean, default=True, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
#     # Relationships
#     subcategories = relationship("Subcategory", back_populates="category", cascade="all, delete-orphan")
#     products = relationship("Product", back_populates="category")

# class Subcategory(Base):
#     __tablename__ = "subcategories"
    
#     subcategory_id = Column(Integer, primary_key=True, index=True)
#     category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
#     name = Column(String(100), nullable=False, index=True)
#     description = Column(Text, nullable=True)
#     is_active = Column(Boolean, default=True, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
#     # Relationships
#     category = relationship("Category", back_populates="subcategories")
#     spec_templates = relationship("SpecificationTemplate", back_populates="subcategory", cascade="all, delete-orphan")
#     products = relationship("Product", back_populates="subcategory")

# class SpecificationTemplate(Base):
#     __tablename__ = "specification_templates"
    
#     template_id = Column(Integer, primary_key=True, index=True)
#     subcategory_id = Column(Integer, ForeignKey("subcategories.subcategory_id"), nullable=False)
#     spec_name = Column(String(100), nullable=False)  # e.g., "RAM", "Size", "Color"
#     spec_type = Column(String(50), nullable=False)   # "select", "text", "number", "boolean"
#     spec_options = Column(JSON, nullable=True)       # For select type: ["6GB", "8GB", "12GB"]
#     is_required = Column(Boolean, default=False)
#     affects_price = Column(Boolean, default=False)   # Whether this spec affects pricing
#     display_order = Column(Integer, default=0)
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
    
#     # Relationships
#     subcategory = relationship("Subcategory", back_populates="spec_templates")
#     price_rules = relationship("PriceRule", back_populates="specification_template", cascade="all, delete-orphan")

# class PriceRule(Base):
#     __tablename__ = "price_rules"
    
#     rule_id = Column(Integer, primary_key=True, index=True)
#     subcategory_id = Column(Integer, ForeignKey("subcategories.subcategory_id"), nullable=False)
#     specification_template_id = Column(Integer, ForeignKey("specification_templates.template_id"), nullable=True)
#     base_price = Column(Integer, nullable=False)  # Base price in cents
#     spec_conditions = Column(JSON, nullable=False)  # {"ram": "8GB", "storage": "256GB"}
#     price_modifier = Column(Integer, default=0)    # Additional price in cents (+200 for premium specs)
#     modifier_type = Column(String(20), default="add")  # "add", "multiply", "set"
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
    
#     # Relationships
#     subcategory = relationship("Subcategory")
#     specification_template = relationship("SpecificationTemplate", back_populates="price_rules")




# src/models/category.py - Clean version for fresh database
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class Category(Base):
    __tablename__ = "categories"
    
    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    subcategories = relationship("Subcategory", back_populates="category", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="category")

class Subcategory(Base):
    __tablename__ = "subcategories"
    
    subcategory_id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="subcategories")
    spec_templates = relationship("SpecificationTemplate", back_populates="subcategory", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="subcategory")

class SpecificationTemplate(Base):
    __tablename__ = "specification_templates"
    
    template_id = Column(Integer, primary_key=True, index=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.subcategory_id"), nullable=False)
    spec_name = Column(String(100), nullable=False)
    spec_type = Column(String(50), nullable=False)  # 'select', 'text', 'number', 'boolean'
    spec_options = Column(JSON, nullable=True)  # For select type
    is_required = Column(Boolean, default=False)
    affects_price = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subcategory = relationship("Subcategory", back_populates="spec_templates")
    price_rules = relationship("PriceRule", back_populates="specification_template", cascade="all, delete-orphan")

class PriceRule(Base):
    __tablename__ = "price_rules"
    
    rule_id = Column(Integer, primary_key=True, index=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.subcategory_id"), nullable=False)
    specification_template_id = Column(Integer, ForeignKey("specification_templates.template_id"), nullable=True)
    base_price = Column(Integer, nullable=False)  # Price in cents
    spec_conditions = Column(JSON, nullable=False)
    price_modifier = Column(Integer, default=0)
    modifier_type = Column(String(20), default="add")  # 'add', 'multiply', 'set'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subcategory = relationship("Subcategory")
    specification_template = relationship("SpecificationTemplate", back_populates="price_rules")
