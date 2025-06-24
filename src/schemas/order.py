# src/schemas/order.py
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.models.order import OrderStatus, PaymentStatus, PaymentMethod
from src.schemas.address import CustomerAddressResponse

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderItemResponse(BaseModel):
    order_item_id: int
    product_id: int
    quantity: int
    unit_price: float
    total_price: float
    product_name: str
    product_description: Optional[str]
    
    class Config:
        from_attributes = True

class PaymentDetails(BaseModel):
    card_number: Optional[str] = None
    card_holder_name: Optional[str] = None
    expiry_date: Optional[str] = None
    cvv: Optional[str] = None

class OrderCreate(BaseModel):
    delivery_address_id: int
    payment_method: PaymentMethod
    payment_details: Optional[PaymentDetails] = None
    special_instructions: Optional[str] = None

class OrderResponse(BaseModel):
    order_id: int
    order_number: str
    customer_id: int
    delivery_address_id: int
    subtotal: float
    tax_amount: float
    shipping_amount: float
    discount_amount: float
    total_amount: float
    order_status: OrderStatus
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    order_date: datetime
    estimated_delivery_date: Optional[datetime]
    tracking_number: Optional[str]
    special_instructions: Optional[str]
    order_items: List[OrderItemResponse]
    delivery_address: CustomerAddressResponse
    
    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total_count: int
    page: int
    size: int

class OrderCreateResponse(BaseModel):
    order_id: int
    order_number: str
    message: str
    total_amount: float