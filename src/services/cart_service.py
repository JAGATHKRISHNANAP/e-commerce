# src/services/cart_service.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from src.models.cart import Cart, CartItem
from src.models.product import Product
from src.models.customer import Customer
from src.schemas.cart import (
    AddToCartRequest, UpdateCartItemRequest,
    CartResponse, CartItemResponse, ProductInCart,
    AddToCartResponse, RemoveFromCartResponse,
    ClearCartResponse, CartSummary
)

class CartService:
    
    @staticmethod
    def get_or_create_cart(customer_id: int, db: Session) -> Cart:
        """Get existing cart or create new one for customer"""
        cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
        
        if not cart:
            cart = Cart(customer_id=customer_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
        
        return cart
    
    @staticmethod
    def add_to_cart(
        customer_id: int,
        request: AddToCartRequest,
        db: Session
    ) -> AddToCartResponse:
        """Add product to customer's cart"""
        try:
            # Get or create cart
            cart = CartService.get_or_create_cart(customer_id, db)
            
            # Check if product exists and has stock
            product = db.query(Product).filter(
                Product.product_id == request.product_id
            ).first()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {request.product_id} not found"
                )
            
            if product.stock_quantity < request.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock. Only {product.stock_quantity} items available"
                )
            
            # Check if item already in cart
            cart_item = db.query(CartItem).filter(
                CartItem.cart_id == cart.cart_id,
                CartItem.product_id == request.product_id
            ).first()
            
            if cart_item:
                # Update quantity if item exists
                new_quantity = cart_item.quantity + request.quantity
                
                if new_quantity > product.stock_quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot add more items. Maximum available: {product.stock_quantity}"
                    )
                
                cart_item.quantity = new_quantity
                cart_item.price_at_time = product.price
                cart_item.updated_at = datetime.utcnow()
                message = "Product quantity updated in cart"
            else:
                # Add new item to cart
                cart_item = CartItem(
                    cart_id=cart.cart_id,
                    product_id=request.product_id,
                    quantity=request.quantity,
                    price_at_time=product.price
                )
                db.add(cart_item)
                message = "Product added to cart"
            
            # Update cart timestamp
            cart.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(cart_item)
            
            # Get cart summary
            cart_summary = CartService.get_cart_summary(cart.cart_id, db)
            
            # Prepare response
            cart_item_response = CartService._build_cart_item_response(cart_item, product)
            
            return AddToCartResponse(
                success=True,
                message=message,
                cart_item=cart_item_response,
                cart_summary=cart_summary
            )
            
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add product to cart"
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add product to cart: {str(e)}"
            )
    
    @staticmethod
    def get_cart(customer_id: int, db: Session) -> CartResponse:
        """Get customer's cart with all items"""
        cart = CartService.get_or_create_cart(customer_id, db)
        
        # Get cart items with product details
        cart_items = db.query(CartItem).filter(
            CartItem.cart_id == cart.cart_id
        ).options(
            joinedload(CartItem.product)
        ).all()
        
        # Build response
        items = []
        total_quantity = 0
        total_amount = Decimal('0.00')
        
        for item in cart_items:
            cart_item_response = CartService._build_cart_item_response(item, item.product)
            items.append(cart_item_response)
            total_quantity += item.quantity
            total_amount += cart_item_response.subtotal
        
        return CartResponse(
            cart_id=cart.cart_id,
            customer_id=cart.customer_id,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
            items=items,
            total_items=len(items),
            total_quantity=total_quantity,
            total_amount=total_amount
        )
    
    @staticmethod
    def update_cart_item(
        customer_id: int,
        product_id: int,
        request: UpdateCartItemRequest,
        db: Session
    ) -> CartItemResponse:
        """Update quantity of item in cart"""
        try:
            # Get customer's cart
            cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
            
            if not cart:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart not found"
                )
            
            # Get cart item
            cart_item = db.query(CartItem).filter(
                CartItem.cart_id == cart.cart_id,
                CartItem.product_id == product_id
            ).first()
            
            if not cart_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found in cart"
                )
            
            # Check stock
            product = cart_item.product
            if request.quantity > product.stock_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock. Only {product.stock_quantity} items available"
                )
            
            # Update quantity
            cart_item.quantity = request.quantity
            cart_item.updated_at = datetime.utcnow()
            cart.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(cart_item)
            
            return CartService._build_cart_item_response(cart_item, product)
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update cart item: {str(e)}"
            )
    
    @staticmethod
    def remove_from_cart(
        customer_id: int,
        product_id: int,
        db: Session
    ) -> RemoveFromCartResponse:
        """Remove item from cart"""
        try:
            # Get customer's cart
            cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
            
            if not cart:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart not found"
                )
            
            # Get cart item
            cart_item = db.query(CartItem).filter(
                CartItem.cart_id == cart.cart_id,
                CartItem.product_id == product_id
            ).first()
            
            if not cart_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found in cart"
                )
            
            # Delete item
            db.delete(cart_item)
            cart.updated_at = datetime.utcnow()
            db.commit()
            
            # Get updated cart summary
            cart_summary = CartService.get_cart_summary(cart.cart_id, db)
            
            return RemoveFromCartResponse(
                success=True,
                message="Product removed from cart",
                cart_summary=cart_summary
            )
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove product from cart: {str(e)}"
            )
    
    @staticmethod
    def clear_cart(customer_id: int, db: Session) -> ClearCartResponse:
        """Clear all items from cart"""
        try:
            # Get customer's cart
            cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
            
            if not cart:
                return ClearCartResponse(
                    success=True,
                    message="Cart is already empty"
                )
            
            # Delete all cart items
            db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).delete()
            cart.updated_at = datetime.utcnow()
            db.commit()
            
            return ClearCartResponse(
                success=True,
                message="Cart cleared successfully"
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clear cart: {str(e)}"
            )
    
    @staticmethod
    def get_cart_summary(cart_id: int, db: Session) -> CartSummary:
        """Get cart summary statistics"""
        cart_items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
        
        total_items = len(cart_items)
        total_quantity = sum(item.quantity for item in cart_items)
        total_amount = sum(
            Decimal(str(item.quantity)) * item.price_at_time 
            for item in cart_items
        )
        
        return CartSummary(
            total_items=total_items,
            total_quantity=total_quantity,
            total_amount=total_amount
        )
    
    @staticmethod
    def _build_cart_item_response(cart_item: CartItem, product: Product) -> CartItemResponse:
        """Build cart item response with product details"""
        product_in_cart = ProductInCart(
            product_id=product.product_id,
            name=product.name,
            description=product.description,
            price=product.price,
            price_at_time=cart_item.price_at_time,
            primary_image_url=product.primary_image_url,
            storage_capacity=product.storage_capacity,
            stock_quantity=product.stock_quantity
        )
        
        subtotal = Decimal(str(cart_item.quantity)) * cart_item.price_at_time
        
        return CartItemResponse(
            cart_item_id=cart_item.cart_item_id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price_at_time=cart_item.price_at_time,
            added_at=cart_item.added_at,
            updated_at=cart_item.updated_at,
            product=product_in_cart,
            subtotal=subtotal
        )