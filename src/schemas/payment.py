
from pydantic import BaseModel
from typing import Optional, Dict, Any

class PaymentOrderCreate(BaseModel):
    amount: float
    currency: str = "INR"

class PaymentOrderResponse(BaseModel):
    id: str
    entity: str
    amount: int
    amount_paid: int
    amount_due: int
    currency: str
    receipt: Optional[str]
    status: str
    attempts: int
    notes: Dict[str, Any]
    created_at: int
    key_id: str  # Send key_id to frontend

class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
