
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from config.database import get_db
from src.services.payment import PaymentService
from src.schemas.payment import PaymentOrderCreate, PaymentOrderResponse, PaymentVerify
from src.models.customer import Customer
from src.api.v1.auth import get_current_user
import os

router = APIRouter()
payment_service = PaymentService()

@router.post("/create-order", response_model=PaymentOrderResponse)
async def create_payment_order(
    order_data: PaymentOrderCreate,
    current_user: Customer = Depends(get_current_user)
):
    """
    Create a Razorpay order id for the frontend to initialize payment.
    """
    try:
        # Create Razorpay order
        # Amount in frontend is usually in standard units (INR), service converts to paise
        order = payment_service.create_order(
            amount=order_data.amount,
            currency=order_data.currency,
            notes={"customer_id": current_user.customer_id}
        )
        
        return {
            **order,
            "key_id": os.getenv('RAZORPAY_KEY_ID')
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/verify")
async def verify_payment(
    payment_data: PaymentVerify,
    current_user: Customer = Depends(get_current_user)
):
    """
    Verify payment signature from Razorpay.
    """
    try:
        payment_service.client.utility.verify_payment_signature({
            'razorpay_order_id': payment_data.razorpay_order_id,
            'razorpay_payment_id': payment_data.razorpay_payment_id,
            'razorpay_signature': payment_data.razorpay_signature
        })
        return {"status": "success", "message": "Payment verified successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed"
        )
