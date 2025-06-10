# src/schemas/product.py
from pydantic import BaseModel
from typing import Optional, List
from .category import CategoryResponse

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category_id: int
    stock_quantity: int = 0
    image_url: Optional[str] = None
    storage_capacity: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    product_id: int
    category: Optional[CategoryResponse] = None
    
    class Config:
        from_attributes = True

class ProductsListResponse(BaseModel):
    products: List[ProductResponse]
    total_count: int
    page: int
    per_page: int
    total_pages: int

