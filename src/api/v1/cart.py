from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.database import get_db
from src.schemas.cart import (
    AddToCartRequest, UpdateCartRequest, RemoveFromCartRequest,
    CartResponse, CartItemResponse
)
from src.services.cart_service import CartService

router = APIRouter()

@router.post("/cart/add")
async def add_to_cart(request: AddToCartRequest, db: Session = Depends(get_db)):
    """Add item to cart"""
    service = CartService(db)
    try:
        return service.add_to_cart(request.session_id, request.product_id, request.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cart/{session_id}", response_model=CartResponse)
async def get_cart(session_id: str, db: Session = Depends(get_db)):
    """Get cart items for a session"""
    service = CartService(db)
    cart_data = service.get_cart(session_id)
    
    # Convert to proper response format
    items = []
    for item in cart_data["items"]:
        items.append(CartItemResponse(
            cart_item_id=item["cart_item_id"],
            product_id=item["product_id"],
            quantity=item["quantity"],
            added_at=item["added_at"],
            product=item["product"],
            subtotal=item["subtotal"]
        ))
    
    return CartResponse(
        items=items,
        total_items=cart_data["total_items"],
        total_amount=cart_data["total_amount"]
    )

@router.put("/cart/{cart_item_id}")
async def update_cart_item(
    cart_item_id: int, 
    request: UpdateCartRequest, 
    db: Session = Depends(get_db)
):
    """Update cart item quantity"""
    service = CartService(db)
    try:
        return service.update_cart_item(cart_item_id, request.session_id, request.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400 if "stock" in str(e) else 404, detail=str(e))

@router.delete("/cart/{cart_item_id}")
async def remove_from_cart(
    cart_item_id: int, 
    request: RemoveFromCartRequest, 
    db: Session = Depends(get_db)
):
    """Remove item from cart"""
    service = CartService(db)
    try:
        return service.remove_from_cart(cart_item_id, request.session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/cart/clear/{session_id}")
async def clear_cart(session_id: str, db: Session = Depends(get_db)):
    """Clear all items from cart"""
    service = CartService(db)
    return service.clear_cart(session_id)

@router.get("/cart/count/{session_id}")
async def get_cart_count(session_id: str, db: Session = Depends(get_db)):
    """Get total number of items in cart"""
    service = CartService(db)
    return service.get_cart_count(session_id)