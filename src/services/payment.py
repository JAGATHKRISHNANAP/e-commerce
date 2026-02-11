
import razorpay
import os
import hmac
import hashlib
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv()

class PaymentService:
    def __init__(self):
        self.key_id = os.getenv('RAZORPAY_KEY_ID')
        self.key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        
        if not self.key_id or not self.key_secret:
            print("Warning: RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET not set in environment")
            # You might want to raise an error here in production
            
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))

    def create_order(self, amount: float, currency: str = "INR", receipt: str = None, notes: dict = None):
        """
        Create a Razorpay order.
        Amount should be provided in standard units (e.g., Rupees), creating logic converts to paise.
        """
        try:
            # Razorpay expects amount in paise (1 INR = 100 paise)
            amount_paise = int(amount * 100)
            
            data = {
                "amount": amount_paise,
                "currency": currency,
                "receipt": receipt,
                "notes": notes or {}
            }
            
            order = self.client.order.create(data=data)
            return order
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating Razorpay order: {str(e)}"
            )

    def verify_payment_signature(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str):
        """
        Verify the payment signature returned by Razorpay.
        """
        try:
            # The client.utility.verify_payment_signature method is preferred if available,
            # but sometimes manual verification is clearer or needed if SDK version differs.
            # Using SDK method:
            self.client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
            return True
        except razorpay.errors.SignatureVerificationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment signature verification failed"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying payment: {str(e)}"
            )
