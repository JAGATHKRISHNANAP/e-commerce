# src/schemas/product_image.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductImageBase(BaseModel):
    image_filename: str
    image_url: str
    alt_text: Optional[str] = None
    is_primary: bool = False
    display_order: int = 0
    uploaded_by: str

class ProductImageCreate(ProductImageBase):
    product_id: int
    image_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

class ProductImageUpdate(BaseModel):
    alt_text: Optional[str] = None
    is_primary: Optional[bool] = None
    display_order: Optional[int] = None

class ProductImageResponse(ProductImageBase):
    image_id: int
    product_id: int
    image_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProductImageListResponse(BaseModel):
    product_id: int
    product_name: str
    total_images: int
    images: list[ProductImageResponse]