# # src/schemas/cart.py
# from pydantic import BaseModel, Field, validator
# from typing import List, Optional
# from datetime import datetime
# from decimal import Decimal

# class AddToCartRequest(BaseModel):
#     product_id: int = Field(..., gt=0, description="Product ID to add to cart")
#     quantity: int = Field(default=1, gt=0, le=100, description="Quantity to add")
    
#     @validator('quantity')
#     def validate_quantity(cls, v):
#         if v <= 0:
#             raise ValueError('Quantity must be greater than 0')
#         if v > 100:
#             raise ValueError('Quantity cannot exceed 100')
#         return v

# class UpdateCartItemRequest(BaseModel):
#     quantity: int = Field(..., gt=0, le=100, description="New quantity")
    
#     @validator('quantity')
#     def validate_quantity(cls, v):
#         if v <= 0:
#             raise ValueError('Quantity must be greater than 0')
#         if v > 100:
#             raise ValueError('Quantity cannot exceed 100')
#         return v

# class ProductInCart(BaseModel):
#     product_id: int
#     name: str
#     description: Optional[str]
#     price: Decimal
#     primary_image_url: Optional[str]
#     storage_capacity: Optional[str]
#     stock_quantity: int
#     category_name: Optional[str]  # ✅ Added this field
    
#     class Config:
#         from_attributes = True

# class CartItemResponse(BaseModel):
#     cart_item_id: int
#     quantity: int
#     price_at_time: Decimal
#     added_at: datetime
#     updated_at: datetime
#     subtotal: Decimal
#     product: ProductInCart  # ✅ Only `product` should contain nested product info
    
#     class Config:
#         from_attributes = True

# class CartResponse(BaseModel):
#     cart_id: int
#     customer_id: int
#     created_at: datetime
#     updated_at: datetime
#     items: List[CartItemResponse]
#     total_items: int
#     total_quantity: int
#     total_amount: Decimal
    
#     class Config:
#         from_attributes = True

# class CartSummary(BaseModel):
#     total_items: int
#     total_quantity: int
#     total_amount: Decimal

# class AddToCartResponse(BaseModel):
#     success: bool
#     message: str
#     cart_item: CartItemResponse
#     cart_summary: CartSummary

# class RemoveFromCartResponse(BaseModel):
#     success: bool
#     message: str
#     cart_summary: CartSummary

# class ClearCartResponse(BaseModel):
#     success: bool
#     message: str

















# src/schemas/cart.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class AddToCartRequest(BaseModel):
    product_id: int = Field(..., gt=0, description="Product ID to add to cart")
    quantity: int = Field(default=1, gt=0, le=100, description="Quantity to add")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        if v > 100:
            raise ValueError('Quantity cannot exceed 100')
        return v

class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(..., gt=0, le=100, description="New quantity")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        if v > 100:
            raise ValueError('Quantity cannot exceed 100')
        return v

class ProductInCart(BaseModel):
    product_id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    primary_image_url: Optional[str] = None
    primary_image_filename: Optional[str] = None  # Made optional and with default
    storage_capacity: Optional[str] = None
    stock_quantity: int
    category_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class CartItemResponse(BaseModel):
    cart_item_id: int
    quantity: int
    price_at_time: Decimal
    added_at: datetime
    updated_at: datetime
    subtotal: Decimal
    product: ProductInCart
    
    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    cart_id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime
    items: List[CartItemResponse]
    total_items: int
    total_quantity: int
    total_amount: Decimal
    
    class Config:
        from_attributes = True

class CartSummary(BaseModel):
    total_items: int
    total_quantity: int
    total_amount: Decimal

class AddToCartResponse(BaseModel):
    success: bool
    message: str
    cart_item: CartItemResponse
    cart_summary: CartSummary

class RemoveFromCartResponse(BaseModel):
    success: bool
    message: str
    cart_summary: CartSummary

class ClearCartResponse(BaseModel):
    success: bool
    message: str