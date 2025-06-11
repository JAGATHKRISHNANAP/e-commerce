# # src/schemas/product.py
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








# # src/schemas/product.py - Updated with image schemas
# from pydantic import BaseModel
# from typing import Optional, List
# from datetime import datetime
# from .category import CategoryResponse
# from .product_image import ProductImageResponse

# class ProductBase(BaseModel):
#     name: str
#     description: Optional[str] = None
#     price: float
#     category_id: int
#     stock_quantity: int = 0
#     storage_capacity: Optional[str] = None

# class ProductCreate(ProductBase):
#     created_by: str  # Sales user who creates the product

# class ProductResponse(ProductBase):
#     product_id: int
#     created_by: str
#     primary_image_url: Optional[str] = None  # Quick access to primary image
#     primary_image_filename: Optional[str] = None
#     category: Optional[CategoryResponse] = None
#     images: List[ProductImageResponse] = []

#     class Config:
#         from_attributes = True

# class ProductsListResponse(BaseModel):
#     products: List[ProductResponse]
#     total_count: int
#     page: int
#     per_page: int
#     total_pages: int

# # src/schemas/product_image.py
# from pydantic import BaseModel
# from typing import Optional
# from datetime import datetime

# class ProductImageBase(BaseModel):
#     image_filename: str
#     image_url: str
#     alt_text: Optional[str] = None
#     is_primary: bool = False
#     display_order: int = 0
#     uploaded_by: str

# class ProductImageCreate(ProductImageBase):
#     product_id: int
#     image_path: str
#     file_size: Optional[int] = None
#     mime_type: Optional[str] = None

# class ProductImageUpdate(BaseModel):
#     alt_text: Optional[str] = None
#     is_primary: Optional[bool] = None
#     display_order: Optional[int] = None

# class ProductImageResponse(ProductImageBase):
#     image_id: int
#     product_id: int
#     image_path: str
#     file_size: Optional[int] = None
#     mime_type: Optional[str] = None
#     created_at: datetime
#     updated_at: datetime

#     class Config:
#         from_attributes = True

# class ProductImageListResponse(BaseModel):
#     product_id: int
#     product_name: str
#     total_images: int
#     images: list[ProductImageResponse]




# # src/schemas/product.py - Updated with image schemas
# from pydantic import BaseModel
# from typing import Optional, List
# from datetime import datetime
# from .category import CategoryResponse
# from .product_image import ProductImageResponse

# class ProductBase(BaseModel):
#     name: str
#     description: Optional[str] = None
#     price: float
#     category_id: int
#     stock_quantity: int = 0
#     storage_capacity: Optional[str] = None

# class ProductCreate(ProductBase):
#     created_by: str  # Sales user who creates the product

# class ProductResponse(ProductBase):
#     product_id: int
#     created_by: str
#     category: Optional[CategoryResponse] = None
#     images: List[ProductImageResponse] = []
    
#     class Config:
#         from_attributes = True

# class ProductsListResponse(BaseModel):
#     products: List[ProductResponse]
#     total_count: int
#     page: int
#     per_page: int
#     total_pages: int



# src/schemas/product.py - Updated with image schemas
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .category import CategoryResponse
from .product_image import ProductImageResponse

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category_id: int
    stock_quantity: int = 0
    storage_capacity: Optional[str] = None

class ProductCreate(ProductBase):
    created_by: str  # Sales user who creates the product

class ProductResponse(ProductBase):
    product_id: int
    created_by: str
    primary_image_url: Optional[str] = None  # Quick access to primary image
    primary_image_filename: Optional[str] = None
    category: Optional[CategoryResponse] = None
    images: List[ProductImageResponse] = []
    
    class Config:
        from_attributes = True

class ProductsListResponse(BaseModel):
    products: List[ProductResponse]
    total_count: int
    page: int
    per_page: int
    total_pages: int