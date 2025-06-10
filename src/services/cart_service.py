
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.cart import CartItem
from src.models.product import Product
from src.models.user import User
from src.api.deps import get_or_create_user
from typing import List, Optional
from datetime import datetime

class CartService:
    def __init__(self, db: Session):
        self.db = db

    def add_to_cart(self, session_id: str, product_id: int, quantity: int) -> dict:
        """Add item to cart"""
        # Check if product exists and has stock
        product = self.db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            raise ValueError("Product not found")
        
        if product.stock_quantity < quantity:
            raise ValueError("Insufficient stock")
        
        # Get or create user
        user = get_or_create_user(session_id, self.db)
        
        # Check if item already exists in cart
        existing_item = self.db.query(CartItem).filter(
            CartItem.user_id == user.user_id,
            CartItem.product_id == product_id
        ).first()
        
        if existing_item:
            # Update quantity
            new_quantity = existing_item.quantity + quantity
            if product.stock_quantity < new_quantity:
                raise ValueError("Insufficient stock for requested quantity")
            existing_item.quantity = new_quantity
            existing_item.added_at = datetime.utcnow()
        else:
            # Create new cart item
            cart_item = CartItem(
                user_id=user.user_id,
                product_id=product_id,
                quantity=quantity
            )
            self.db.add(cart_item)
        
        self.db.commit()
        return {"message": "Item added to cart successfully"}

    def get_cart(self, session_id: str) -> dict:
        """Get cart items for a session"""
        user = self.db.query(User).filter(User.session_id == session_id).first()
        if not user:
            return {"items": [], "total_items": 0, "total_amount": 0.0}
        
        cart_items = self.db.query(CartItem).filter(CartItem.user_id == user.user_id).all()
        
        items = []
        total_amount = 0.0
        total_items = 0
        
        for cart_item in cart_items:
            subtotal = float(cart_item.product.price * cart_item.quantity)
            items.append({
                "cart_item_id": cart_item.cart_item_id,
                "product_id": cart_item.product_id,
                "quantity": cart_item.quantity,
                "added_at": cart_item.added_at,
                "product": cart_item.product,
                "subtotal": subtotal
            })
            total_amount += subtotal
            total_items += cart_item.quantity
        
        return {
            "items": items,
            "total_items": total_items,
            "total_amount": total_amount
        }

    def update_cart_item(self, cart_item_id: int, session_id: str, quantity: int) -> dict:
        """Update cart item quantity"""
        user = get_or_create_user(session_id, self.db)
        
        cart_item = self.db.query(CartItem).filter(
            CartItem.cart_item_id == cart_item_id,
            CartItem.user_id == user.user_id
        ).first()
        
        if not cart_item:
            raise ValueError("Cart item not found")
        
        # Check stock
        if cart_item.product.stock_quantity < quantity:
            raise ValueError("Insufficient stock")
        
        cart_item.quantity = quantity
        cart_item.added_at = datetime.utcnow()
        self.db.commit()
        
        return {"message": "Cart item updated successfully"}

    def remove_from_cart(self, cart_item_id: int, session_id: str) -> dict:
        """Remove item from cart"""
        user = get_or_create_user(session_id, self.db)
        
        cart_item = self.db.query(CartItem).filter(
            CartItem.cart_item_id == cart_item_id,
            CartItem.user_id == user.user_id
        ).first()
        
        if not cart_item:
            raise ValueError("Cart item not found")
        
        self.db.delete(cart_item)
        self.db.commit()
        
        return {"message": "Item removed from cart successfully"}

    def clear_cart(self, session_id: str) -> dict:
        """Clear all items from cart"""
        user = self.db.query(User).filter(User.session_id == session_id).first()
        if not user:
            return {"message": "Cart is already empty"}
        
        self.db.query(CartItem).filter(CartItem.user_id == user.user_id).delete()
        self.db.commit()
        
        return {"message": "Cart cleared successfully"}

    def get_cart_count(self, session_id: str) -> dict:
        """Get total number of items in cart"""
        user = self.db.query(User).filter(User.session_id == session_id).first()
        if not user:
            return {"count": 0}
        
        result = self.db.query(func.sum(CartItem.quantity)).filter(CartItem.user_id == user.user_id).scalar()
        count = result if result else 0
        
        return {"count": count}