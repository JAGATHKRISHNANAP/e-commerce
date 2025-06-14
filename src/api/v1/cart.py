# # src/api/v1/cart.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from config.database import get_db
from src.schemas.cart import (
    AddToCartRequest, UpdateCartItemRequest,
    CartResponse, AddToCartResponse,
    RemoveFromCartResponse, ClearCartResponse,CartItemResponse
)
from src.services.cart_service import CartService
from src.models.customer import Customer
from src.api.v1.auth import get_current_user

router = APIRouter()

@router.post("/cart/add", response_model=AddToCartResponse)
async def add_to_cart(
    request: AddToCartRequest,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a product to the current user's cart.
    
    - Requires authentication
    - Creates a cart if user doesn't have one
    - Updates quantity if product already in cart
    - Validates stock availability
    """
    return CartService.add_to_cart(
        customer_id=current_user.customer_id,
        request=request,
        db=db
    )

@router.get("/cart", response_model=CartResponse)
async def get_cart(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's cart with all items.
    
    - Requires authentication
    - Returns empty cart if no items
    - Includes product details and calculated totals
    """
    return CartService.get_cart(
        customer_id=current_user.customer_id,
        db=db
    )

@router.put("/cart/item/{product_id}", response_model=CartItemResponse)
async def update_cart_item(
    product_id: int,
    request: UpdateCartItemRequest,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update quantity of a product in cart.
    
    - Requires authentication
    - Validates stock availability
    - Product must already be in cart
    """
    return CartService.update_cart_item(
        customer_id=current_user.customer_id,
        product_id=product_id,
        request=request,
        db=db
    )

@router.delete("/cart/item/{product_id}", response_model=RemoveFromCartResponse)
async def remove_from_cart(
    product_id: int,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a product from cart.
    
    - Requires authentication
    - Returns updated cart summary
    """
    return CartService.remove_from_cart(
        customer_id=current_user.customer_id,
        product_id=product_id,
        db=db
    )

@router.delete("/cart/clear", response_model=ClearCartResponse)
async def clear_cart(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clear all items from cart.
    
    - Requires authentication
    - Removes all items at once
    """
    return CartService.clear_cart(
        customer_id=current_user.customer_id,
        db=db
    )

@router.get("/cart/count")
async def get_cart_count(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get quick cart count for navbar/header display.
    
    - Requires authentication
    - Returns total unique items and total quantity
    """
    cart = CartService.get_or_create_cart(current_user.customer_id, db)
    cart_summary = CartService.get_cart_summary(cart.cart_id, db)
    
    return {
        "total_items": cart_summary.total_items,
        "total_quantity": cart_summary.total_quantity
    }




