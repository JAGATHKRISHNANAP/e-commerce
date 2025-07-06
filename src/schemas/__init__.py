# src/schemas/__init__.py
from .category import CategoryResponse, CategoryCreate
from .product import ProductResponse, ProductCreate, ProductsListResponse
from .product_image import (
    ProductImageResponse, 
    ProductImageCreate, 
    ProductImageUpdate,
    ProductImageListResponse
)
from .cart import (
    CartResponse, 
    AddToCartRequest, 
    UpdateCartItemRequest, 
    CartItemResponse
)

from .specification_template import (
    SpecificationTemplateResponse,SpecificationTemplateCreate, SpecificationTemplateUpdate
)

__all__ = [
    "CategoryResponse", 
    "CategoryCreate",
    "ProductResponse", 
    "ProductCreate", 
    "ProductsListResponse",
    "ProductImageResponse",
    "ProductImageCreate",
    "ProductImageUpdate", 
    "ProductImageListResponse",
    # ====================================
    "CartResponse",
    "AddToCartRequest",
    "UpdateCartItemRequest",
    "CartItemResponse"

    # =-================================
    "SpecificationTemplateResponse",
    "SpecificationTemplateCreate",
    "SpecificationTemplateUpdate"

]