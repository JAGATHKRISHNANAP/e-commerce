from pydantic import BaseModel
from typing import List
from datetime import datetime
from .product import ProductResponse

class AddToCartRequest(BaseModel):
    session_id: str
    product_id: int
    quantity: int = 1

class UpdateCartRequest(BaseModel):
    session_id: str
    quantity: int

class RemoveFromCartRequest(BaseModel):
    session_id: str

class CartItemResponse(BaseModel):
    cart_item_id: int
    product_id: int
    quantity: int
    added_at: datetime
    product: ProductResponse
    subtotal: float
    
    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_items: int
    total_amount: float