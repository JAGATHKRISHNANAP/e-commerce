from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import os
import requests
import json
from urllib.parse import quote
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from config.database import get_db
from src.models.order import Order, OrderItem, OrderStatus
from src.models.product import Product
from src.models.vendor import Vendor
from src.api.v1.vender_auth import get_current_user as get_current_vendor

router = APIRouter()

class VisionUrlRequest(BaseModel):
    email: str

@router.post('/get-vison-url')
def get_vison_url(request: VisionUrlRequest):
    email = request.email
    secret_key = os.getenv("VISION_SECRET_KEY", "4608545fc18c8ed7ef90cb3838c014bb5362b73bfa14f9d539651b8d08470e2a")

    try:
        response = requests.post(
            "http://localhost:5000/api/third-party-login",
            json={
                "secret_key": secret_key,
                "email": email
            },
            headers={"Content-Type": "application/json"}
        )
        
        # In case the response is not valid JSON
        try:
            data = response.json()
        except Exception:
            raise HTTPException(status_code=500, detail="Invalid response from 3Avision")

        if data.get("status") == "success":
            user_data = data.get("user", {})
            user_param = quote(json.dumps(user_data))
            access_token = data.get("access_token", "")
            
            sso_url = f"http://localhost:3000/sso-auth?token={access_token}&user={user_param}&redirect=/dashboard_view"
            
            return {"ssoUrl": sso_url}
        else:
            raise HTTPException(status_code=401, detail="Unauthorized by 3Avision")
            
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="Error connecting to 3Avision")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


class OrderSummary(BaseModel):
    total: int
    pending: int
    processing: int
    shipped: int
    delivered: int
    cancelled: int
    revenue_total: float
    revenue_this_month: float


class ProductSummary(BaseModel):
    total: int
    low_stock: int
    out_of_stock: int


class RecentOrderItem(BaseModel):
    id: int
    order_number: str
    customer_name: str
    status: str
    payment_status: Optional[str] = None
    total_amount: float
    created_at: datetime


class VendorSummaryResponse(BaseModel):
    orders: OrderSummary
    products: ProductSummary
    recent_orders: List[RecentOrderItem]


@router.get('/summary', response_model=VendorSummaryResponse)
def get_vendor_summary(
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    """Aggregate counts, revenue, and the latest orders for the signed-in vendor."""
    vendor_identifier = current_vendor.vendor_ph_no

    # --- Orders: counts per status (distinct orders, since an order can hold
    # many of this vendor's items) ---
    base_orders_q = (
        db.query(Order.order_id, Order.order_status)
        .join(OrderItem, OrderItem.order_id == Order.order_id)
        .join(Product, Product.product_id == OrderItem.product_id)
        .filter(Product.created_by == vendor_identifier)
        .distinct()
    )
    rows = base_orders_q.all()
    counts = {
        'total': len(rows),
        'pending': 0, 'processing': 0, 'shipped': 0,
        'delivered': 0, 'cancelled': 0,
    }
    for _, s in rows:
        key = s.value if hasattr(s, 'value') else str(s or '').lower()
        if key in counts:
            counts[key] += 1

    # --- Revenue: sum of line totals for this vendor's items on non-cancelled orders ---
    revenue_total_q = (
        db.query(func.coalesce(func.sum(OrderItem.total_price), 0))
        .join(Product, Product.product_id == OrderItem.product_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .filter(
            Product.created_by == vendor_identifier,
            Order.order_status != OrderStatus.CANCELLED,
        )
    )
    revenue_total = float(revenue_total_q.scalar() or 0)

    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    revenue_month_q = (
        db.query(func.coalesce(func.sum(OrderItem.total_price), 0))
        .join(Product, Product.product_id == OrderItem.product_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .filter(
            Product.created_by == vendor_identifier,
            Order.order_status != OrderStatus.CANCELLED,
            Order.created_at >= month_start,
        )
    )
    revenue_this_month = float(revenue_month_q.scalar() or 0)

    # --- Products ---
    products_total = db.query(func.count(Product.product_id)).filter(
        Product.created_by == vendor_identifier
    ).scalar() or 0
    products_low = db.query(func.count(Product.product_id)).filter(
        Product.created_by == vendor_identifier,
        Product.stock_quantity > 0,
        Product.stock_quantity <= 5,
    ).scalar() or 0
    products_out = db.query(func.count(Product.product_id)).filter(
        Product.created_by == vendor_identifier,
        Product.stock_quantity == 0,
    ).scalar() or 0

    # --- Recent orders (distinct, last 5 by created_at) ---
    recent_query = (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.order_id)
        .join(Product, Product.product_id == OrderItem.product_id)
        .filter(Product.created_by == vendor_identifier)
        .options(
            joinedload(Order.order_items).joinedload(OrderItem.product),
            joinedload(Order.customer),
        )
        .distinct()
        .order_by(Order.created_at.desc())
        .limit(5)
    )

    recent = []
    for order in recent_query.all():
        vendor_subtotal = sum(
            (item.total_price or 0)
            for item in order.order_items
            if item.product and item.product.created_by == vendor_identifier
        )
        customer_name = (
            order.customer.customer_name if order.customer and order.customer.customer_name
            else f"Customer #{order.customer_id}"
        )
        recent.append(RecentOrderItem(
            id=order.order_id,
            order_number=order.order_number,
            customer_name=customer_name,
            status=order.order_status,
            payment_status=order.payment_status.value if order.payment_status else None,
            total_amount=float(vendor_subtotal),
            created_at=order.created_at,
        ))

    return VendorSummaryResponse(
        orders=OrderSummary(
            total=counts['total'],
            pending=counts['pending'],
            processing=counts['processing'],
            shipped=counts['shipped'],
            delivered=counts['delivered'],
            cancelled=counts['cancelled'],
            revenue_total=revenue_total,
            revenue_this_month=revenue_this_month,
        ),
        products=ProductSummary(
            total=int(products_total),
            low_stock=int(products_low),
            out_of_stock=int(products_out),
        ),
        recent_orders=recent,
    )
