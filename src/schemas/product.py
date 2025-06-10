# from pydantic import BaseModel
# from typing import Optional, List
# from .category import CategoryResponse

# class ProductBase(BaseModel):
#     name: str
#     description: Optional[str] = None
#     price: float
#     category_id: int
#     stock_quantity: int = 0
#     image_url: Optional[str] = None
#     storage_capacity: Optional[str] = None

# class ProductCreate(ProductBase):
#     pass

# class ProductResponse(ProductBase):
#     product_id: int
#     category: Optional[CategoryResponse] = None
    
#     class Config:
#         from_attributes = True

# class ProductsListResponse(BaseModel):
#     products: List[ProductResponse]
#     total_count: int
#     page: int
#     per_page: int
#     total_pages: int








# src/schemas/product.py - Fixed for Pydantic v2 Compatibility

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# ========== Product Image Schemas ==========

class ProductImageBase(BaseModel):
    image_url: str = Field(..., description="Image URL")
    alt_text: Optional[str] = Field(None, max_length=200, description="Alternative text for image")
    is_primary: bool = Field(False, description="Whether this is the primary image")
    display_order: int = Field(0, ge=0, description="Display order of the image")

class ProductImageCreate(ProductImageBase):
    pass

class ProductImageResponse(ProductImageBase):
    image_id: int
    product_id: int

    class Config:
        from_attributes = True

# ========== Product Schemas ==========

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: Decimal = Field(..., gt=0, description="Product price")
    category_id: int = Field(..., gt=0, description="Category ID")
    stock_quantity: int = Field(0, ge=0, description="Stock quantity")
    sku: Optional[str] = Field(None, max_length=100, description="Stock Keeping Unit")
    is_active: bool = Field(True, description="Whether product is active")
    
    # Additional attributes
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    weight: Optional[Decimal] = Field(None, gt=0, description="Weight in grams")
    dimensions: Optional[str] = Field(None, max_length=100, description="Product dimensions")
    color: Optional[str] = Field(None, max_length=50, description="Product color")
    size: Optional[str] = Field(None, max_length=50, description="Product size")
    material: Optional[str] = Field(None, max_length=100, description="Product material")

    @field_validator('price', 'weight')
    @classmethod
    def validate_decimal_places(cls, v):
        if v is not None:
            # Ensure maximum 2 decimal places
            decimal_tuple = v.as_tuple()
            if decimal_tuple.exponent < -2:
                raise ValueError('Maximum 2 decimal places allowed')
        return v

class ProductCreate(ProductBase):
    """Schema for creating a new product"""
    pass

class ProductUpdate(BaseModel):
    """Schema for updating an existing product - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    category_id: Optional[int] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    brand: Optional[str] = Field(None, max_length=100)
    weight: Optional[Decimal] = Field(None, gt=0)
    dimensions: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=50)
    material: Optional[str] = Field(None, max_length=100)

    @field_validator('price', 'weight')
    @classmethod
    def validate_decimal_places(cls, v):
        if v is not None:
            # Ensure maximum 2 decimal places
            decimal_tuple = v.as_tuple()
            if decimal_tuple.exponent < -2:
                raise ValueError('Maximum 2 decimal places allowed')
        return v

class ProductResponse(BaseModel):
    """Schema for returning detailed product information"""
    product_id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    stock_quantity: int = 0
    sku: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    # Additional attributes
    brand: Optional[str] = None
    weight: Optional[Decimal] = None
    dimensions: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None
    
    # Related data
    images: List[ProductImageResponse] = []
    primary_image_url: Optional[str] = None

    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    """Schema for product list items (simplified)"""
    product_id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    category_name: Optional[str] = None
    primary_image_url: Optional[str] = None
    stock_quantity: int = 0
    is_active: bool = True
    brand: Optional[str] = None

    class Config:
        from_attributes = True

class ProductsListResponse(BaseModel):
    """Schema for paginated product lists"""
    products: List[ProductListResponse]
    total_count: int
    page: int = 1
    per_page: int = 20
    total_pages: int

# ========== Alternative naming for compatibility ==========

# These are aliases for backward compatibility with your existing code
ProductsResponse = ProductsListResponse  # Alternative name
ProductDetailResponse = ProductResponse  # Alternative name