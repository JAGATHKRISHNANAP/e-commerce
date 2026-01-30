from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from config.database import get_db
from src.models.order import Order, OrderItem, OrderStatus
from src.models.product import Product
from src.models.vendor import Vendor
from src.api.v1.vender_auth import get_current_user as get_current_vendor
from pydantic import BaseModel

router = APIRouter()

# --- Schemas ---

class VendorOrderItemResponse(BaseModel):
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    product_image: Optional[str] = None

class VendorOrderResponse(BaseModel):
    order_id: int
    order_number: str
    order_date: datetime
    customer_name: Optional[str] # Or just ID if not available
    status: str
    total_amount: float # This is the order total, maybe we calculate vendor subtotal too?
    items: List[VendorOrderItemResponse]
    shipping_address: Optional[str] = None

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    tracking_number: Optional[str] = None

# --- Endpoints ---

@router.get("/orders", response_model=List[VendorOrderResponse])
async def get_vendor_orders(
    status: Optional[str] = None,
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    """
    Get all orders that contain products created by this vendor.
    """
    # Find products by this vendor
    # We assume 'created_by' in Product matches vendor_ph_no or potentially vendor_name. 
    # To be safe, checking both or relying on ph_no which is unique.
    
    vendor_identifier = current_vendor.vendor_ph_no
    
    # Query Orders that have items matching this vendor's products
    orders = db.query(Order).join(OrderItem).join(Product).filter(
        Product.created_by == vendor_identifier
    ).options(
        joinedload(Order.order_items).joinedload(OrderItem.product),
        joinedload(Order.delivery_address),
        joinedload(Order.customer)
    ).distinct().all()

    # Apply status filter if provided
    if status and status.lower() != 'all orders':
        # API usually receives lowercase, but strict check
        orders = [o for o in orders if o.order_status.lower() == status.lower()]

    # Transform to response
    response = []
    for order in orders:
        # Filter items for this vendor
        vendor_items = []
        vendor_order_total = 0.0
        
        for item in order.order_items:
            if item.product.created_by == vendor_identifier:
                vendor_items.append(VendorOrderItemResponse(
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    product_image=item.product.primary_image_url
                ))
                vendor_order_total += item.total_price

        # Skip if somehow no items for this vendor (shouldn't happen due to filter)
        if not vendor_items:
            continue
            
        # Format address
        addr = order.delivery_address
        address_str = f"{addr.address_line1}, {addr.city}, {addr.state} - {addr.pincode}" if addr else "N/A"
        
        # Get customer name
        customer_name = order.customer.customer_name if order.customer else f"Customer #{order.customer_id}"
        
        response.append(VendorOrderResponse(
            order_id=order.order_id,
            order_number=order.order_number,
            order_date=order.created_at,
            customer_name=customer_name,
            status=order.order_status,
            total_amount=vendor_order_total, # Showing total for THIS vendor's items only
            items=vendor_items,
            shipping_address=address_str
        ))

    return response

@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    update_data: OrderStatusUpdate,
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    """
    Update status of an order. 
    NOTE: This updates the Global Order Status. 
    """
    # 1. Verify order contains vendor's products
    vendor_identifier = current_vendor.vendor_ph_no
    
    # Check if order exists and belongs to vendor (at least partially)
    order = db.query(Order).join(OrderItem).join(Product).filter(
        Order.order_id == order_id,
        Product.created_by == vendor_identifier
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or you do not have permission to modify it"
        )

    # 2. Update status
    order.order_status = update_data.status
    if update_data.tracking_number:
        order.tracking_number = update_data.tracking_number
        
    # If Delivered, set delivered_date
    if update_data.status == OrderStatus.DELIVERED:
        order.delivered_date = datetime.now()
        
    db.commit()
    db.refresh(order)
    
    return {"message": "Order status updated successfully", "status": order.order_status}
