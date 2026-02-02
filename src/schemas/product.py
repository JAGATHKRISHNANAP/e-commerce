# src/schemas/product.py - Fixed for Pydantic v2
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime
from .product_image import ProductImageResponse

# Import only for type checking
if TYPE_CHECKING:
    from .category import CategoryResponse
    from .subcategory import SubcategoryResponse

class ProductImageOnly(BaseModel):
    primary_image_url: Optional[str] = None
    primary_image_filename: Optional[str] = None
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    specifications: Dict[str, Any] = Field(default_factory=dict)
    base_price: int = Field(..., gt=0)  # Price in cents
    stock_quantity: int = Field(default=0, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    group_id: Optional[str] = Field(None, max_length=50)
    is_active: bool = True

class ProductCreate(ProductBase):
    category_id: int
    subcategory_id: int
    created_by: str = Field(..., min_length=1, max_length=100)

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    base_price: Optional[int] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    group_id: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    product_id: int
    category_id: int
    subcategory_id: int
    calculated_price: int  # Final price after applying rules
    primary_image_url: Optional[str] = None
    primary_image_filename: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    # These will be populated by the API if needed
    category: Optional[Dict[str, Any]] = None
    subcategory: Optional[Dict[str, Any]] = None
    
    images: List[ProductImageResponse] = []
    variants: List[Dict[str, Any]] = []  # List of related variant products
    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total_count: int
    page: int
    per_page: int
    total_pages: int

# Pricing-related schemas
class PriceCalculationRequest(BaseModel):
    subcategory_id: int
    specifications: Dict[str, Any]
    base_price: int = Field(..., gt=0)  # Made required for consistency

    @field_validator('specifications')
    @classmethod
    def validate_specifications(cls, v):
        if not isinstance(v, dict):
            raise ValueError('specifications must be a dictionary')
        return v

class AppliedRule(BaseModel):
    rule_id: int
    rule_name: Optional[str] = None
    modifier_type: str
    modifier_value: int
    conditions_matched: Dict[str, Any]

class PriceCalculationResponse(BaseModel):
    base_price: int
    calculated_price: int
    applied_rules: List[AppliedRule] = []
    price_breakdown: Dict[str, int] = Field(default_factory=dict)

# Keep backward compatibility alias
ProductsListResponse = ProductListResponse