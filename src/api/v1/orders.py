# # src/api/v1/orders.py
# from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
# from sqlalchemy.orm import Session, joinedload
# from sqlalchemy import desc
# from typing import List, Optional
# from datetime import datetime, timedelta
# import secrets
# import string
# from config.database import get_db
# from src.models.order import Order, OrderItem
# from src.models.product import Product
# from src.models.cart import CartItem
# from src.models.address import CustomerAddress
# from src.schemas.order import OrderCreate, OrderResponse, OrderListResponse, OrderCreateResponse
# # from src.services.auth import get_current_user
# from src.api.v1.auth import get_current_user

# router = APIRouter()

# def generate_order_number() -> str:
#     """Generate a unique order number"""
#     timestamp = datetime.now().strftime("%Y%m%d")
#     random_part = ''.join(secrets.choice(string.digits) for _ in range(6))
#     return f"ORD{timestamp}{random_part}"

# async def update_product_stock(db: Session, product_id: int, quantity: int):
#     """Update product stock after order placement"""
#     product = db.query(Product).filter(Product.product_id == product_id).first()
#     if product:
#         if product.stock_quantity >= quantity:
#             product.stock_quantity -= quantity
#             db.commit()
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"Insufficient stock for product {product.name}. Available: {product.stock_quantity}, Requested: {quantity}"
#             )

# async def clear_customer_cart(db: Session, customer_id: int):
#     """Clear customer cart after successful order"""
#     db.query(CartItem).filter(CartItem.customer_id == customer_id).delete()
#     db.commit()

# @router.post("/orders", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
# async def create_order(
#     order_data: OrderCreate,
#     background_tasks: BackgroundTasks,
#     customer_id: int = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Create a new order from cart items"""
    
#     # Verify delivery address belongs to customer
#     delivery_address = db.query(CustomerAddress).filter(
#         CustomerAddress.address_id == order_data.delivery_address_id,
#         CustomerAddress.customer_id == customer_id,
#         CustomerAddress.is_active == True
#     ).first()
    
#     if not delivery_address:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Delivery address not found"
#         )
    
#     # Get cart items
#     cart_items = db.query(CartItem).options(
#         joinedload(CartItem.product)
#     ).filter(CartItem.customer_id == customer_id).all()
    
#     if not cart_items:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Cart is empty"
#         )
    
#     # Check stock availability for all items
#     for cart_item in cart_items:
#         if cart_item.product.stock_quantity < cart_item.quantity:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"Insufficient stock for {cart_item.product.name}. Available: {cart_item.product.stock_quantity}, Requested: {cart_item.quantity}"
#             )
    
#     # Calculate totals
#     subtotal = sum(float(cart_item.product.price) * cart_item.quantity for cart_item in cart_items)
#     tax_rate = 0.18  # 18% GST
#     tax_amount = subtotal * tax_rate
#     shipping_amount = 0.0  # Free shipping
#     discount_amount = 0.0  # No discount for now
#     total_amount = subtotal + tax_amount + shipping_amount - discount_amount
    
#     # Create order
#     order_number = generate_order_number()
#     order = Order(
#         order_number=order_number,
#         customer_id=customer_id,
#         delivery_address_id=order_data.delivery_address_id,
#         subtotal=subtotal,
#         tax_amount=tax_amount,
#         shipping_amount=shipping_amount,
#         discount_amount=discount_amount,
#         total_amount=total_amount,
#         payment_method=order_data.payment_method,
#         special_instructions=order_data.special_instructions,
#         estimated_delivery_date=datetime.now() + timedelta(days=5)  # 5 days from now
#     )
    
#     db.add(order)
#     db.flush()  # To get the order_id
    
#     # Create order items and update stock
#     for cart_item in cart_items:
#         order_item = OrderItem(
#             order_id=order.order_id,
#             product_id=cart_item.product_id,
#             quantity=cart_item.quantity,
#             unit_price=float(cart_item.product.price),
#             total_price=float(cart_item.product.price) * cart_item.quantity,
#             product_name=cart_item.product.name,
#             product_description=cart_item.product.description
#         )
#         db.add(order_item)
        
#         # Update product stock
#         await update_product_stock(db, cart_item.product_id, cart_item.quantity)
    
#     # Commit the transaction
#     db.commit()
#     db.refresh(order)
    
#     # Clear cart in background
#     background_tasks.add_task(clear_customer_cart, db, customer_id)
    
#     return OrderCreateResponse(
#         order_id=order.order_id,
#         order_number=order.order_number,
#         message="Order placed successfully!",
#         total_amount=order.total_amount
#     )

# @router.get("/orders", response_model=OrderListResponse)
# async def get_customer_orders(
#     page: int = 1,
#     size: int = 10,
#     customer_id: int = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get customer's order history"""
#     offset = (page - 1) * size
    
#     orders_query = db.query(Order).options(
#         joinedload(Order.order_items),
#         joinedload(Order.delivery_address)
#     ).filter(Order.customer_id == customer_id)
    
#     total_count = orders_query.count()
#     orders = orders_query.order_by(desc(Order.created_at)).offset(offset).limit(size).all()
    
#     return OrderListResponse(
#         orders=orders,
#         total_count=total_count,
#         page=page,
#         size=size
#     )

# @router.get("/orders/{order_id}", response_model=OrderResponse)
# async def get_order(
#     order_id: int,
#     customer_id: int = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get a specific order"""
#     order = db.query(Order).options(
#         joinedload(Order.order_items),
#         joinedload(Order.delivery_address)
#     ).filter(
#         Order.order_id == order_id,
#         Order.customer_id == customer_id
#     ).first()
    
#     if not order:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Order not found"
#         )
    
#     return order

# @router.patch("/orders/{order_id}/cancel")
# async def cancel_order(
#     order_id: int,
#     customer_id: int = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Cancel an order (only if it's not shipped)"""
#     order = db.query(Order).filter(
#         Order.order_id == order_id,
#         Order.customer_id == customer_id
#     ).first()
    
#     if not order:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Order not found"
#         )
    
#     if order.order_status in ["shipped", "delivered", "cancelled"]:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Cannot cancel order with status: {order.order_status}"
#         )
    
#     # Update order status
#     order.order_status = "cancelled"
#     order.cancelled_date = datetime.now()
    
#     # Restore product stock
#     order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
#     for item in order_items:
#         product = db.query(Product).filter(Product.product_id == item.product_id).first()
#         if product:
#             product.stock_quantity += item.quantity
    
#     db.commit()
    
#     return {"message": "Order cancelled successfully", "order_id": order_id}


# from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
# from sqlalchemy.orm import Session, joinedload
# from sqlalchemy import desc
# from typing import List, Optional
# from datetime import datetime, timedelta
# import secrets
# import string

# from config.database import get_db
# from src.models.order import Order, OrderItem
# from src.models.product import Product
# from src.models.cart import CartItem, Cart
# from src.models.address import CustomerAddress
# from src.models.customer import Customer
# from src.schemas.order import OrderCreate, OrderResponse, OrderListResponse, OrderCreateResponse
# from src.api.v1.auth import get_current_user

# router = APIRouter()


# def generate_order_number() -> str:
#     timestamp = datetime.now().strftime("%Y%m%d")
#     random_part = ''.join(secrets.choice(string.digits) for _ in range(6))
#     return f"ORD{timestamp}{random_part}"


# async def update_product_stock(db: Session, product_id: int, quantity: int):
#     product = db.query(Product).filter(Product.product_id == product_id).first()
#     if product:
#         if product.stock_quantity >= quantity:
#             product.stock_quantity -= quantity
#             db.commit()
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"Insufficient stock for product {product.name}. Available: {product.stock_quantity}, Requested: {quantity}"
#             )


# async def clear_customer_cart(db: Session, customer_id: int):
#     db.query(CartItem).filter(CartItem.customer_id == customer_id).delete()
#     db.commit()


# # @router.post("/orders", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
# # async def create_order(
# #     order_data: OrderCreate,
# #     background_tasks: BackgroundTasks,
# #     customer: Customer = Depends(get_current_user),
# #     db: Session = Depends(get_db)
# # ):
# #     customer_id = customer.customer_id

# #     delivery_address = db.query(CustomerAddress).filter(
# #         CustomerAddress.address_id == order_data.delivery_address_id,
# #         CustomerAddress.customer_id == customer_id,
# #         CustomerAddress.is_active == True
# #     ).first()

# #     if not delivery_address:
# #         raise HTTPException(
# #             status_code=status.HTTP_404_NOT_FOUND,
# #             detail="Delivery address not found"
# #         )

# #     cart_items = db.query(CartItem).options(
# #         joinedload(CartItem.product)
# #     ).filter(CartItem.customer_id == customer_id).all()

# #     if not cart_items:
# #         raise HTTPException(
# #             status_code=status.HTTP_400_BAD_REQUEST,
# #             detail="Cart is empty"
# #         )

# #     for cart_item in cart_items:
# #         if cart_item.product.stock_quantity < cart_item.quantity:
# #             raise HTTPException(
# #                 status_code=status.HTTP_400_BAD_REQUEST,
# #                 detail=f"Insufficient stock for {cart_item.product.name}. Available: {cart_item.product.stock_quantity}, Requested: {cart_item.quantity}"
# #             )

# #     subtotal = sum(float(cart_item.product.price) * cart_item.quantity for cart_item in cart_items)
# #     tax_rate = 0.18
# #     tax_amount = subtotal * tax_rate
# #     shipping_amount = 0.0
# #     discount_amount = 0.0
# #     total_amount = subtotal + tax_amount + shipping_amount - discount_amount

# #     order_number = generate_order_number()
# #     order = Order(
# #         order_number=order_number,
# #         customer_id=customer_id,
# #         delivery_address_id=order_data.delivery_address_id,
# #         subtotal=subtotal,
# #         tax_amount=tax_amount,
# #         shipping_amount=shipping_amount,
# #         discount_amount=discount_amount,
# #         total_amount=total_amount,
# #         payment_method=order_data.payment_method,
# #         special_instructions=order_data.special_instructions,
# #         estimated_delivery_date=datetime.now() + timedelta(days=5)
# #     )

# #     db.add(order)
# #     db.flush()

# #     for cart_item in cart_items:
# #         order_item = OrderItem(
# #             order_id=order.order_id,
# #             product_id=cart_item.product_id,
# #             quantity=cart_item.quantity,
# #             unit_price=float(cart_item.product.price),
# #             total_price=float(cart_item.product.price) * cart_item.quantity,
# #             product_name=cart_item.product.name,
# #             product_description=cart_item.product.description
# #         )
# #         db.add(order_item)
# #         await update_product_stock(db, cart_item.product_id, cart_item.quantity)

# #     db.commit()
# #     db.refresh(order)

# #     background_tasks.add_task(clear_customer_cart, db, customer_id)

# #     return OrderCreateResponse(
# #         order_id=order.order_id,
# #         order_number=order.order_number,
# #         message="Order placed successfully!",
# #         total_amount=order.total_amount
# #     )
# @router.post("/orders", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
# async def create_order(
#     order_data: OrderCreate,
#     background_tasks: BackgroundTasks,
#     customer: Customer = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     customer_id = customer.customer_id

#     delivery_address = db.query(CustomerAddress).filter(
#         CustomerAddress.address_id == order_data.delivery_address_id,
#         CustomerAddress.customer_id == customer_id,
#         CustomerAddress.is_active == True
#     ).first()

#     if not delivery_address:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Delivery address not found"
#         )

#     # Fixed: Join CartItem with Cart to access customer_id
#     cart_items = db.query(CartItem).options(
#         joinedload(CartItem.product)
#     ).join(Cart).filter(Cart.customer_id == customer_id).all()

#     if not cart_items:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Cart is empty"
#         )

#     for cart_item in cart_items:
#         if cart_item.product.stock_quantity < cart_item.quantity:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"Insufficient stock for {cart_item.product.name}. Available: {cart_item.product.stock_quantity}, Requested: {cart_item.quantity}"
#             )

#     subtotal = sum(float(cart_item.product.price) * cart_item.quantity for cart_item in cart_items)
#     tax_rate = 0.18
#     tax_amount = subtotal * tax_rate
#     shipping_amount = 0.0
#     discount_amount = 0.0
#     total_amount = subtotal + tax_amount + shipping_amount - discount_amount

#     order_number = generate_order_number()
#     order = Order(
#         order_number=order_number,
#         customer_id=customer_id,
#         delivery_address_id=order_data.delivery_address_id,
#         subtotal=subtotal,
#         tax_amount=tax_amount,
#         shipping_amount=shipping_amount,
#         discount_amount=discount_amount,
#         total_amount=total_amount,
#         payment_method=order_data.payment_method,
#         special_instructions=order_data.special_instructions,
#         estimated_delivery_date=datetime.now() + timedelta(days=5)
#     )

#     db.add(order)
#     db.flush()

#     for cart_item in cart_items:
#         order_item = OrderItem(
#             order_id=order.order_id,
#             product_id=cart_item.product_id,
#             quantity=cart_item.quantity,
#             unit_price=float(cart_item.product.price),
#             total_price=float(cart_item.product.price) * cart_item.quantity,
#             product_name=cart_item.product.name,
#             product_description=cart_item.product.description
#         )
#         db.add(order_item)
#         await update_product_stock(db, cart_item.product_id, cart_item.quantity)

#     db.commit()
#     db.refresh(order)

#     background_tasks.add_task(clear_customer_cart, db, customer_id)

#     return OrderCreateResponse(
#         order_id=order.order_id,
#         order_number=order.order_number,
#         message="Order placed successfully!",
#         total_amount=order.total_amount
#     )




# @router.get("/orders", response_model=OrderListResponse)
# async def get_customer_orders(
#     page: int = 1,
#     size: int = 10,
#     customer: Customer = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     customer_id = customer.customer_id
#     offset = (page - 1) * size

#     orders_query = db.query(Order).options(
#         joinedload(Order.order_items),
#         joinedload(Order.delivery_address)
#     ).filter(Order.customer_id == customer_id)

#     total_count = orders_query.count()
#     orders = orders_query.order_by(desc(Order.created_at)).offset(offset).limit(size).all()

#     return OrderListResponse(
#         orders=orders,
#         total_count=total_count,
#         page=page,
#         size=size
#     )


# @router.get("/orders/{order_id}", response_model=OrderResponse)
# async def get_order(
#     order_id: int,
#     customer: Customer = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     customer_id = customer.customer_id

#     order = db.query(Order).options(
#         joinedload(Order.order_items),
#         joinedload(Order.delivery_address)
#     ).filter(
#         Order.order_id == order_id,
#         Order.customer_id == customer_id
#     ).first()

#     if not order:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Order not found"
#         )

#     return order









from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import secrets
import string

from config.database import get_db
from src.models.order import Order, OrderItem, PaymentStatus, PaymentMethod
from src.models.product import Product
from src.models.cart import CartItem, Cart
from src.models.address import CustomerAddress
from src.models.customer import Customer
from src.schemas.order import OrderCreate, OrderResponse, OrderListResponse, OrderCreateResponse
from src.api.v1.auth import get_current_user

router = APIRouter()


def get_product_price(product: Product) -> Decimal:
    """Get the effective price for a product, handling the new pricing structure"""
    if product.calculated_price is not None:
        return Decimal(str(product.calculated_price)) / Decimal('100')  # Convert cents to dollars
    elif product.base_price is not None:
        return Decimal(str(product.base_price)) / Decimal('100')  # Convert cents to dollars
    elif product.price is not None:
        return product.price
    else:
        raise ValueError(f"Product {product.product_id} has no price set")


def generate_order_number() -> str:
    timestamp = datetime.now().strftime("%Y%m%d")
    random_part = ''.join(secrets.choice(string.digits) for _ in range(6))
    return f"ORD{timestamp}{random_part}"


async def update_product_stock(db: Session, product_id: int, quantity: int):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if product:
        if product.stock_quantity >= quantity:
            product.stock_quantity -= quantity
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product.name}. Available: {product.stock_quantity}, Requested: {quantity}"
            )


async def clear_customer_cart(db: Session, customer_id: int):
    """
    Clear all cart items for a specific customer.
    This function handles the case where CartItem doesn't have direct customer_id.
    """
    try:
        # Find the customer's cart
        cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
        
        if cart:
            # Delete all items in the cart
            deleted_count = db.query(CartItem).filter(
                CartItem.cart_id == cart.cart_id
            ).delete()
            
            db.commit()
            print(f"Cleared {deleted_count} items from cart for customer {customer_id}")
        else:
            print(f"No cart found for customer {customer_id}")
            
    except Exception as e:
        db.rollback()
        print(f"Error clearing cart for customer {customer_id}: {str(e)}")
        raise e


@router.post("/orders", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    customer: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer_id = customer.customer_id

    delivery_address = db.query(CustomerAddress).filter(
        CustomerAddress.address_id == order_data.delivery_address_id,
        CustomerAddress.customer_id == customer_id,
        CustomerAddress.is_active == True
    ).first()

    if not delivery_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery address not found"
        )

    # Fixed: Join CartItem with Cart to access customer_id
    cart_items = db.query(CartItem).options(
        joinedload(CartItem.product)
    ).join(Cart).filter(Cart.customer_id == customer_id).all()

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    # Validate stock and collect price information
    order_details = []
    
    # Verify Payment if Razorpay
    if order_data.payment_method == PaymentMethod.RAZORPAY:
        if not all([order_data.razorpay_order_id, order_data.razorpay_payment_id, order_data.razorpay_signature]):
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Razorpay payment details"
            )
        try:
            from src.services.payment import PaymentService
            payment_service = PaymentService()
            payment_service.verify_payment_signature(
                razorpay_order_id=order_data.razorpay_order_id,
                razorpay_payment_id=order_data.razorpay_payment_id,
                razorpay_signature=order_data.razorpay_signature
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment verification failed: {str(e)}"
            )

    for cart_item in cart_items:
        if cart_item.product.stock_quantity < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {cart_item.product.name}. Available: {cart_item.product.stock_quantity}, Requested: {cart_item.quantity}"
            )
        
        # Use price_at_time from cart (this is the price when item was added to cart)
        # If price_at_time is None, fall back to current product price
        if cart_item.price_at_time is not None:
            item_price = cart_item.price_at_time
        else:
            try:
                item_price = get_product_price(cart_item.product)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        order_details.append({
            'cart_item': cart_item,
            'price': item_price,
            'total': float(item_price) * cart_item.quantity
        })

    # Calculate order totals using the collected price information
    # Calculate totals
    subtotal = sum(detail['total'] for detail in order_details)
    
    # Standardized Logic:
    # 1. Discount: 15% off MRP
    discount_rate = 0.15
    discount_amount = subtotal * discount_rate
    
    # 2. Tax: 18% GST on the discounted price (actual selling price)
    tax_rate = 0.18
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * tax_rate
    
    # 3. Shipping: Free if order value (after discount) > 499, else 40
    shipping_amount = 0.0 if taxable_amount > 499 else 40.0
    
    # 4. Total Amount
    total_amount = taxable_amount + tax_amount + shipping_amount

    order_number = generate_order_number()
    order = Order(
        order_number=order_number,
        customer_id=customer_id,
        delivery_address_id=order_data.delivery_address_id,
        subtotal=subtotal,
        tax_amount=tax_amount,
        shipping_amount=shipping_amount,
        discount_amount=discount_amount,
        total_amount=total_amount,
        payment_method=order_data.payment_method,
        special_instructions=order_data.special_instructions,
        estimated_delivery_date=datetime.now() + timedelta(days=5)
    )

    if order_data.payment_method == PaymentMethod.RAZORPAY:
        order.payment_status = PaymentStatus.PAID
        order.payment_reference = order_data.razorpay_payment_id
        order.payment_gateway_response = f"order_id:{order_data.razorpay_order_id}, signature:{order_data.razorpay_signature}"

    db.add(order)
    db.flush()

    # Create order items using the price information we collected
    for detail in order_details:
        cart_item = detail['cart_item']
        item_price = detail['price']
        
        order_item = OrderItem(
            order_id=order.order_id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            unit_price=float(item_price),
            total_price=float(item_price) * cart_item.quantity,
            product_name=cart_item.product.name,
            product_description=cart_item.product.description
        )
        db.add(order_item)
        await update_product_stock(db, cart_item.product_id, cart_item.quantity)

    db.commit()
    db.refresh(order)

    background_tasks.add_task(clear_customer_cart, db, customer_id)

    return OrderCreateResponse(
        order_id=order.order_id,
        order_number=order.order_number,
        message="Order placed successfully!",
        total_amount=order.total_amount
    )


@router.get("/orders", response_model=OrderListResponse)
async def get_customer_orders(
    page: int = 1,
    size: int = 10,
    customer: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer_id = customer.customer_id
    offset = (page - 1) * size

    orders_query = db.query(Order).options(
        joinedload(Order.order_items).joinedload(OrderItem.product),
        joinedload(Order.delivery_address)
    ).filter(Order.customer_id == customer_id)

    total_count = orders_query.count()
    orders = orders_query.order_by(desc(Order.created_at)).offset(offset).limit(size).all()

    return OrderListResponse(
        orders=orders,
        total_count=total_count,
        page=page,
        size=size
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    customer: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer_id = customer.customer_id

    order = db.query(Order).options(
        joinedload(Order.order_items).joinedload(OrderItem.product),
        joinedload(Order.delivery_address)
    ).filter(
        Order.order_id == order_id,
        Order.customer_id == customer_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return order


@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    customer: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer_id = customer.customer_id

    order = db.query(Order).filter(
        Order.order_id == order_id,
        Order.customer_id == customer_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.order_status in ["shipped", "delivered", "cancelled", "returned", "return_requested"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status: {order.order_status}"
        )

    order.order_status = "cancelled"
    order.cancelled_date = datetime.now()

    # Restore stock
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    for item in order_items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        if product:
            product.stock_quantity += item.quantity

    db.commit()

    return {"message": "Order cancelled successfully", "order_id": order_id}


@router.post("/orders/{order_id}/return")
async def return_order(
    order_id: int,
    customer: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer_id = customer.customer_id

    order = db.query(Order).filter(
        Order.order_id == order_id,
        Order.customer_id == customer_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.order_status != "delivered":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only delivered orders can be returned"
        )
        
    if not order.delivered_date:
        # Fallback if delivered_date is missing but status is delivered
        order.delivered_date = datetime.now()

    # Check 9-day return window
    current_time = datetime.now(order.delivered_date.tzinfo) if order.delivered_date.tzinfo else datetime.now()
    delta = current_time - order.delivered_date
    if delta.days > 9:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Return period expired (9 days limit)"
        )

    order.order_status = "return_requested"
    db.commit()

    return {"message": "Return request submitted successfully", "order_id": order_id}















# from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
# from sqlalchemy.orm import Session, joinedload
# from sqlalchemy import desc
# from typing import List, Optional
# from datetime import datetime, timedelta
# import secrets
# import string

# from config.database import get_db
# from src.models.order import Order, OrderItem
# from src.models.product import Product
# from src.models.cart import CartItem, Cart
# from src.models.address import CustomerAddress
# from src.models.customer import Customer
# from src.schemas.order import OrderCreate, OrderResponse, OrderListResponse, OrderCreateResponse
# from src.api.v1.auth import get_current_user

# router = APIRouter()


# def generate_order_number() -> str:
#     timestamp = datetime.now().strftime("%Y%m%d")
#     random_part = ''.join(secrets.choice(string.digits) for _ in range(6))
#     return f"ORD{timestamp}{random_part}"


# async def update_product_stock(db: Session, product_id: int, quantity: int):
#     product = db.query(Product).filter(Product.product_id == product_id).first()
#     if product:
#         if product.stock_quantity >= quantity:
#             product.stock_quantity -= quantity
#             db.commit()
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"Insufficient stock for product {product.name}. Available: {product.stock_quantity}, Requested: {quantity}"
#             )


# # async def clear_customer_cart(db: Session, customer_id: int):
# #     # Fixed: Join CartItem with Cart to access customer_id
# #     db.query(CartItem).join(Cart).filter(Cart.customer_id == customer_id).delete(synchronize_session=False)
# #     db.commit()
# async def clear_customer_cart(db: Session, customer_id: int):
#     """
#     Clear all cart items for a specific customer.
#     This function handles the case where CartItem doesn't have direct customer_id.
#     """
#     try:
#         # Find the customer's cart
#         cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
        
#         if cart:
#             # Delete all items in the cart
#             deleted_count = db.query(CartItem).filter(
#                 CartItem.cart_id == cart.cart_id
#             ).delete()
            
#             db.commit()
#             print(f"Cleared {deleted_count} items from cart for customer {customer_id}")
#         else:
#             print(f"No cart found for customer {customer_id}")
            
#     except Exception as e:
#         db.rollback()
#         print(f"Error clearing cart for customer {customer_id}: {str(e)}")
#         raise e


# @router.post("/orders", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
# async def create_order(
#     order_data: OrderCreate,
#     background_tasks: BackgroundTasks,
#     customer: Customer = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     customer_id = customer.customer_id

#     delivery_address = db.query(CustomerAddress).filter(
#         CustomerAddress.address_id == order_data.delivery_address_id,
#         CustomerAddress.customer_id == customer_id,
#         CustomerAddress.is_active == True
#     ).first()

#     if not delivery_address:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Delivery address not found"
#         )

#     # Fixed: Join CartItem with Cart to access customer_id
#     cart_items = db.query(CartItem).options(
#         joinedload(CartItem.product)
#     ).join(Cart).filter(Cart.customer_id == customer_id).all()

#     if not cart_items:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Cart is empty"
#         )

#     for cart_item in cart_items:
#         if cart_item.product.stock_quantity < cart_item.quantity:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"Insufficient stock for {cart_item.product.name}. Available: {cart_item.product.stock_quantity}, Requested: {cart_item.quantity}"
#             )

#     subtotal = sum(float(cart_item.product.price) * cart_item.quantity for cart_item in cart_items)
#     tax_rate = 0.18
#     tax_amount = subtotal * tax_rate
#     shipping_amount = 0.0
#     discount_amount = 0.0
#     total_amount = subtotal + tax_amount + shipping_amount - discount_amount

#     order_number = generate_order_number()
#     order = Order(
#         order_number=order_number,
#         customer_id=customer_id,
#         delivery_address_id=order_data.delivery_address_id,
#         subtotal=subtotal,
#         tax_amount=tax_amount,
#         shipping_amount=shipping_amount,
#         discount_amount=discount_amount,
#         total_amount=total_amount,
#         payment_method=order_data.payment_method,
#         special_instructions=order_data.special_instructions,
#         estimated_delivery_date=datetime.now() + timedelta(days=5)
#     )

#     db.add(order)
#     db.flush()

#     for cart_item in cart_items:
#         order_item = OrderItem(
#             order_id=order.order_id,
#             product_id=cart_item.product_id,
#             quantity=cart_item.quantity,
#             unit_price=float(cart_item.product.price),
#             total_price=float(cart_item.product.price) * cart_item.quantity,
#             product_name=cart_item.product.name,
#             product_description=cart_item.product.description
#         )
#         db.add(order_item)
#         await update_product_stock(db, cart_item.product_id, cart_item.quantity)

#     db.commit()
#     db.refresh(order)

#     background_tasks.add_task(clear_customer_cart, db, customer_id)

#     return OrderCreateResponse(
#         order_id=order.order_id,
#         order_number=order.order_number,
#         message="Order placed successfully!",
#         total_amount=order.total_amount
#     )


# @router.get("/orders", response_model=OrderListResponse)
# async def get_customer_orders(
#     page: int = 1,
#     size: int = 10,
#     customer: Customer = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     customer_id = customer.customer_id
#     offset = (page - 1) * size

#     orders_query = db.query(Order).options(
#         joinedload(Order.order_items),
#         joinedload(Order.delivery_address)
#     ).filter(Order.customer_id == customer_id)

#     total_count = orders_query.count()
#     orders = orders_query.order_by(desc(Order.created_at)).offset(offset).limit(size).all()

#     return OrderListResponse(
#         orders=orders,
#         total_count=total_count,
#         page=page,
#         size=size
#     )


# @router.get("/orders/{order_id}", response_model=OrderResponse)
# async def get_order(
#     order_id: int,
#     customer: Customer = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     customer_id = customer.customer_id

#     order = db.query(Order).options(
#         joinedload(Order.order_items),
#         joinedload(Order.delivery_address)
#     ).filter(
#         Order.order_id == order_id,
#         Order.customer_id == customer_id
#     ).first()

#     if not order:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Order not found"
#         )

#     return order


# @router.patch("/orders/{order_id}/cancel")
# async def cancel_order(
#     order_id: int,
#     customer: Customer = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     customer_id = customer.customer_id

#     order = db.query(Order).filter(
#         Order.order_id == order_id,
#         Order.customer_id == customer_id
#     ).first()

#     if not order:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Order not found"
#         )

#     if order.order_status in ["shipped", "delivered", "cancelled"]:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Cannot cancel order with status: {order.order_status}"
#         )

#     order.order_status = "cancelled"
#     order.cancelled_date = datetime.now()

#     # Restore stock for cancelled items
#     order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
#     for item in order_items:
#         product = db.query(Product).filter(Product.product_id == item.product_id).first()
#         if product:
#             product.stock_quantity += item.quantity

#     db.commit()

#     return {"message": "Order cancelled successfully", "order_id": order_id}