# # # from fastapi import FastAPI, HTTPException, Depends, Query
# # # from fastapi.middleware.cors import CORSMiddleware
# # # from sqlalchemy import create_engine, Column, Integer, String, Text, DECIMAL, ForeignKey, Index, DateTime, Boolean
# # # from sqlalchemy.ext.declarative import declarative_base
# # # from sqlalchemy.orm import sessionmaker, Session, relationship
# # # from pydantic import BaseModel
# # # from typing import List, Optional
# # # from datetime import datetime
# # # import os
# # # from dotenv import load_dotenv
# # # import urllib.parse

# # # load_dotenv()

# # # # Database configuration
# # # DB_NAME = 'e-commerce'
# # # USER_NAME = 'postgres'
# # # PASSWORD = 'jaTHU@12'
# # # HOST = 'localhost'
# # # PORT = '5432'

# # # # URL encode the password to handle special characters
# # # encoded_password = urllib.parse.quote_plus(PASSWORD)
# # # DATABASE_URL = f"postgresql://{USER_NAME}:{encoded_password}@{HOST}:{PORT}/{DB_NAME}"

# # # engine = create_engine(DATABASE_URL)
# # # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# # # Base = declarative_base()

# # # # Database Models
# # # class Category(Base):
# # #     __tablename__ = "categories"
    
# # #     category_id = Column(Integer, primary_key=True, index=True)
# # #     name = Column(String(100), unique=True, nullable=False)
    
# # #     products = relationship("Product", back_populates="category")

# # # class Product(Base):
# # #     __tablename__ = "products"
    
# # #     product_id = Column(Integer, primary_key=True, index=True)
# # #     name = Column(String(255), nullable=False, index=True)
# # #     description = Column(Text)
# # #     price = Column(DECIMAL(10, 2), nullable=False)
# # #     category_id = Column(Integer, ForeignKey("categories.category_id"))
# # #     stock_quantity = Column(Integer, default=0)
# # #     image_url = Column(Text)
# # #     storage_capacity = Column(String(50))
    
# # #     category = relationship("Category", back_populates="products")
# # #     cart_items = relationship("CartItem", back_populates="product")

# # # class User(Base):
# # #     __tablename__ = "users"
    
# # #     user_id = Column(Integer, primary_key=True, index=True)
# # #     session_id = Column(String(255), unique=True, nullable=False, index=True)
# # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # #     cart_items = relationship("CartItem", back_populates="user")

# # # class CartItem(Base):
# # #     __tablename__ = "cart_items"
    
# # #     cart_item_id = Column(Integer, primary_key=True, index=True)
# # #     user_id = Column(Integer, ForeignKey("users.user_id"))
# # #     product_id = Column(Integer, ForeignKey("products.product_id"))
# # #     quantity = Column(Integer, nullable=False, default=1)
# # #     added_at = Column(DateTime, default=datetime.utcnow)
    
# # #     user = relationship("User", back_populates="cart_items")
# # #     product = relationship("Product", back_populates="cart_items")

# # # # Create indexes
# # # Index('idx_products_category_id', Product.category_id)
# # # Index('idx_products_name', Product.name)
# # # Index('idx_cart_items_user_id', CartItem.user_id)
# # # Index('idx_cart_items_product_id', CartItem.product_id)

# # # # Pydantic Models
# # # class CategoryResponse(BaseModel):
# # #     category_id: int
# # #     name: str
    
# # #     class Config:
# # #         from_attributes = True

# # # class ProductResponse(BaseModel):
# # #     product_id: int
# # #     name: str
# # #     description: Optional[str]
# # #     price: float
# # #     category_id: int
# # #     stock_quantity: int
# # #     image_url: Optional[str]
# # #     storage_capacity: Optional[str]
# # #     category: Optional[CategoryResponse]
    
# # #     class Config:
# # #         from_attributes = True

# # # class ProductsListResponse(BaseModel):
# # #     products: List[ProductResponse]
# # #     total_count: int
# # #     page: int
# # #     per_page: int
# # #     total_pages: int

# # # class AddToCartRequest(BaseModel):
# # #     session_id: str
# # #     product_id: int
# # #     quantity: int = 1

# # # class UpdateCartRequest(BaseModel):
# # #     session_id: str
# # #     quantity: int

# # # class CartItemResponse(BaseModel):
# # #     cart_item_id: int
# # #     product_id: int
# # #     quantity: int
# # #     added_at: datetime
# # #     product: ProductResponse
# # #     subtotal: float
    
# # #     class Config:
# # #         from_attributes = True

# # # class CartResponse(BaseModel):
# # #     items: List[CartItemResponse]
# # #     total_items: int
# # #     total_amount: float

# # # class RemoveFromCartRequest(BaseModel):
# # #     session_id: str

# # # # FastAPI App
# # # app = FastAPI(title="E-commerce API with Cart", version="1.0.0")

# # # # CORS middleware
# # # app.add_middleware(
# # #     CORSMiddleware,
# # #     allow_origins=["http://localhost:3000", "http://localhost:5173"],
# # #     allow_credentials=True,
# # #     allow_methods=["*"],
# # #     allow_headers=["*"],
# # # )

# # # # Create tables
# # # Base.metadata.create_all(bind=engine)

# # # # Dependency to get database session
# # # def get_db():
# # #     db = SessionLocal()
# # #     try:
# # #         yield db
# # #     finally:
# # #         db.close()

# # # def get_or_create_user(session_id: str, db: Session):
# # #     """Get or create a user based on session_id"""
# # #     user = db.query(User).filter(User.session_id == session_id).first()
# # #     if not user:
# # #         user = User(session_id=session_id)
# # #         db.add(user)
# # #         db.commit()
# # #         db.refresh(user)
# # #     return user

# # # # Product API Endpoints (existing)
# # # @app.get("/api/categories", response_model=List[CategoryResponse])
# # # async def get_categories(db: Session = Depends(get_db)):
# # #     """Get all categories"""
# # #     categories = db.query(Category).all()
# # #     return categories

# # # @app.get("/api/products", response_model=ProductsListResponse)
# # # async def get_products(
# # #     page: int = Query(1, ge=1),
# # #     per_page: int = Query(20, ge=1, le=100),
# # #     category_id: Optional[int] = Query(None),
# # #     search: Optional[str] = Query(None),
# # #     min_price: Optional[float] = Query(None, ge=0),
# # #     max_price: Optional[float] = Query(None, ge=0),
# # #     sort_by: Optional[str] = Query("name", regex="^(name|price|stock_quantity)$"),
# # #     sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$"),
# # #     db: Session = Depends(get_db)
# # # ):
# # #     """Get products with filtering, searching, and pagination"""
# # #     query = db.query(Product)
    
# # #     # Apply filters
# # #     if category_id:
# # #         query = query.filter(Product.category_id == category_id)
    
# # #     if search:
# # #         query = query.filter(Product.name.ilike(f"%{search}%"))
    
# # #     if min_price is not None:
# # #         query = query.filter(Product.price >= min_price)
    
# # #     if max_price is not None:
# # #         query = query.filter(Product.price <= max_price)
    
# # #     # Apply sorting
# # #     if sort_order == "desc":
# # #         query = query.order_by(getattr(Product, sort_by).desc())
# # #     else:
# # #         query = query.order_by(getattr(Product, sort_by).asc())
    
# # #     # Get total count
# # #     total_count = query.count()
    
# # #     # Apply pagination
# # #     offset = (page - 1) * per_page
# # #     products = query.offset(offset).limit(per_page).all()
    
# # #     # Calculate total pages
# # #     total_pages = (total_count + per_page - 1) // per_page
    
# # #     return ProductsListResponse(
# # #         products=products,
# # #         total_count=total_count,
# # #         page=page,
# # #         per_page=per_page,
# # #         total_pages=total_pages
# # #     )

# # # @app.get("/api/products/{product_id}", response_model=ProductResponse)
# # # async def get_product(product_id: int, db: Session = Depends(get_db)):
# # #     """Get a single product by ID"""
# # #     product = db.query(Product).filter(Product.product_id == product_id).first()
# # #     if not product:
# # #         raise HTTPException(status_code=404, detail="Product not found")
# # #     return product

# # # @app.get("/api/products/featured", response_model=List[ProductResponse])
# # # async def get_featured_products(limit: int = Query(8, ge=1, le=20), db: Session = Depends(get_db)):
# # #     """Get featured products (top selling or latest)"""
# # #     products = db.query(Product).filter(Product.stock_quantity > 0).limit(limit).all()
# # #     return products

# # # @app.get("/api/search/suggestions")
# # # async def get_search_suggestions(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
# # #     """Get search suggestions based on product names"""
# # #     suggestions = db.query(Product.name).filter(
# # #         Product.name.ilike(f"%{q}%")
# # #     ).distinct().limit(10).all()
    
# # #     return [suggestion[0] for suggestion in suggestions]

# # # @app.get("/api/price-range")
# # # async def get_price_range(category_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
# # #     """Get min and max price range for products"""
# # #     query = db.query(Product)
    
# # #     if category_id:
# # #         query = query.filter(Product.category_id == category_id)
    
# # #     from sqlalchemy import func
# # #     result = query.with_entities(
# # #         func.min(Product.price).label('min_price'),
# # #         func.max(Product.price).label('max_price')
# # #     ).first()
    
# # #     return {
# # #         "min_price": float(result.min_price) if result.min_price else 0,
# # #         "max_price": float(result.max_price) if result.max_price else 0
# # #     }

# # # # Cart API Endpoints
# # # @app.post("/api/cart/add")
# # # async def add_to_cart(request: AddToCartRequest, db: Session = Depends(get_db)):
# # #     """Add item to cart"""
# # #     # Check if product exists and has stock
# # #     product = db.query(Product).filter(Product.product_id == request.product_id).first()
# # #     if not product:
# # #         raise HTTPException(status_code=404, detail="Product not found")
    
# # #     if product.stock_quantity < request.quantity:
# # #         raise HTTPException(status_code=400, detail="Insufficient stock")
    
# # #     # Get or create user
# # #     user = get_or_create_user(request.session_id, db)
    
# # #     # Check if item already exists in cart
# # #     existing_item = db.query(CartItem).filter(
# # #         CartItem.user_id == user.user_id,
# # #         CartItem.product_id == request.product_id
# # #     ).first()
    
# # #     if existing_item:
# # #         # Update quantity
# # #         new_quantity = existing_item.quantity + request.quantity
# # #         if product.stock_quantity < new_quantity:
# # #             raise HTTPException(status_code=400, detail="Insufficient stock for requested quantity")
# # #         existing_item.quantity = new_quantity
# # #         existing_item.added_at = datetime.utcnow()
# # #     else:
# # #         # Create new cart item
# # #         cart_item = CartItem(
# # #             user_id=user.user_id,
# # #             product_id=request.product_id,
# # #             quantity=request.quantity
# # #         )
# # #         db.add(cart_item)
    
# # #     db.commit()
    
# # #     return {"message": "Item added to cart successfully"}

# # # @app.get("/api/cart/{session_id}", response_model=CartResponse)
# # # async def get_cart(session_id: str, db: Session = Depends(get_db)):
# # #     """Get cart items for a session"""
# # #     user = db.query(User).filter(User.session_id == session_id).first()
# # #     if not user:
# # #         return CartResponse(items=[], total_items=0, total_amount=0.0)
    
# # #     cart_items = db.query(CartItem).filter(CartItem.user_id == user.user_id).all()
    
# # #     items = []
# # #     total_amount = 0.0
# # #     total_items = 0
    
# # #     for cart_item in cart_items:
# # #         subtotal = float(cart_item.product.price * cart_item.quantity)
# # #         items.append(CartItemResponse(
# # #             cart_item_id=cart_item.cart_item_id,
# # #             product_id=cart_item.product_id,
# # #             quantity=cart_item.quantity,
# # #             added_at=cart_item.added_at,
# # #             product=cart_item.product,
# # #             subtotal=subtotal
# # #         ))
# # #         total_amount += subtotal
# # #         total_items += cart_item.quantity
    
# # #     return CartResponse(
# # #         items=items,
# # #         total_items=total_items,
# # #         total_amount=total_amount
# # #     )

# # # @app.put("/api/cart/{cart_item_id}")
# # # async def update_cart_item(
# # #     cart_item_id: int, 
# # #     request: UpdateCartRequest, 
# # #     db: Session = Depends(get_db)
# # # ):
# # #     """Update cart item quantity"""
# # #     # Verify user owns this cart item
# # #     user = get_or_create_user(request.session_id, db)
    
# # #     cart_item = db.query(CartItem).filter(
# # #         CartItem.cart_item_id == cart_item_id,
# # #         CartItem.user_id == user.user_id
# # #     ).first()
    
# # #     if not cart_item:
# # #         raise HTTPException(status_code=404, detail="Cart item not found")
    
# # #     # Check stock
# # #     if cart_item.product.stock_quantity < request.quantity:
# # #         raise HTTPException(status_code=400, detail="Insufficient stock")
    
# # #     cart_item.quantity = request.quantity
# # #     cart_item.added_at = datetime.utcnow()
# # #     db.commit()
    
# # #     return {"message": "Cart item updated successfully"}

# # # @app.delete("/api/cart/{cart_item_id}")
# # # async def remove_from_cart(
# # #     cart_item_id: int, 
# # #     request: RemoveFromCartRequest, 
# # #     db: Session = Depends(get_db)
# # # ):
# # #     """Remove item from cart"""
# # #     # Verify user owns this cart item
# # #     user = get_or_create_user(request.session_id, db)
    
# # #     cart_item = db.query(CartItem).filter(
# # #         CartItem.cart_item_id == cart_item_id,
# # #         CartItem.user_id == user.user_id
# # #     ).first()
    
# # #     if not cart_item:
# # #         raise HTTPException(status_code=404, detail="Cart item not found")
    
# # #     db.delete(cart_item)
# # #     db.commit()
    
# # #     return {"message": "Item removed from cart successfully"}

# # # @app.delete("/api/cart/clear/{session_id}")
# # # async def clear_cart(session_id: str, db: Session = Depends(get_db)):
# # #     """Clear all items from cart"""
# # #     user = db.query(User).filter(User.session_id == session_id).first()
# # #     if not user:
# # #         return {"message": "Cart is already empty"}
    
# # #     db.query(CartItem).filter(CartItem.user_id == user.user_id).delete()
# # #     db.commit()
    
# # #     return {"message": "Cart cleared successfully"}

# # # @app.get("/api/cart/count/{session_id}")
# # # async def get_cart_count(session_id: str, db: Session = Depends(get_db)):
# # #     """Get total number of items in cart"""
# # #     user = db.query(User).filter(User.session_id == session_id).first()
# # #     if not user:
# # #         return {"count": 0}
    
# # #     from sqlalchemy import func
# # #     result = db.query(func.sum(CartItem.quantity)).filter(CartItem.user_id == user.user_id).scalar()
# # #     count = result if result else 0
    
# # #     return {"count": count}

# # # if __name__ == "__main__":
# # #     import uvicorn
# # #     uvicorn.run(app, host="0.0.0.0", port=8000)









# # # # app.py
# # # from fastapi import FastAPI
# # # from fastapi.middleware.cors import CORSMiddleware
# # # from config.database import engine
# # # from src.models import Base
# # # from src.api.v1 import categories, products, cart
# # # import uvicorn

# # # # Create tables
# # # Base.metadata.create_all(bind=engine)

# # # def create_app() -> FastAPI:
# # #     """Create FastAPI application with all configurations"""
    
# # #     app = FastAPI(
# # #         title="E-commerce API with Cart",
# # #         version="1.0.0",
# # #         description="A comprehensive e-commerce API with product management and shopping cart functionality"
# # #     )

# # #     # CORS middleware
# # #     app.add_middleware(
# # #         CORSMiddleware,
# # #         allow_origins=["http://localhost:3000", "http://localhost:5173"],
# # #         allow_credentials=True,
# # #         allow_methods=["*"],
# # #         allow_headers=["*"],
# # #     )

# # #     # Include API routers
# # #     app.include_router(categories.router, prefix="/api/v1", tags=["categories"])
# # #     app.include_router(products.router, prefix="/api/v1", tags=["products"])
# # #     app.include_router(cart.router, prefix="/api/v1", tags=["cart"])

# # #     @app.get("/")
# # #     async def root():
# # #         return {
# # #             "message": "E-commerce API",
# # #             "version": "1.0.0",
# # #             "status": "running"
# # #         }

# # #     @app.get("/health")
# # #     async def health_check():
# # #         return {"status": "healthy"}

# # #     return app

# # # app = create_app()

# # # if __name__ == "__main__":
# # #     uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)


# # # app.py
# # from fastapi import FastAPI
# # from fastapi.middleware.cors import CORSMiddleware
# # from fastapi.staticfiles import StaticFiles
# # from config.database import engine
# # from src.models import Base
# # from src.api.v1 import categories, products, cart
# # import uvicorn
# # import os

# # # Create tables
# # Base.metadata.create_all(bind=engine)

# # def create_app() -> FastAPI:
# #     """Create FastAPI application with all configurations"""
    
# #     app = FastAPI(
# #         title="E-commerce API with Cart",
# #         version="1.0.0",
# #         description="A comprehensive e-commerce API with product management and shopping cart functionality"
# #     )

# #     # CORS middleware
# #     app.add_middleware(
# #         CORSMiddleware,
# #         allow_origins=["http://localhost:3000", "http://localhost:5173"],
# #         allow_credentials=True,
# #         allow_methods=["*"],
# #         allow_headers=["*"],
# #     )

# #     # Create uploads directory if it doesn't exist
# #     os.makedirs("uploads", exist_ok=True)
    
# #     # Mount static files for serving uploaded images
# #     app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# #     # Include API routers
# #     app.include_router(categories.router, prefix="/api/v1", tags=["categories"])
# #     app.include_router(products.router, prefix="/api/v1", tags=["products"])
# #     app.include_router(cart.router, prefix="/api/v1", tags=["cart"])

# #     @app.get("/")
# #     async def root():
# #         return {
# #             "message": "E-commerce API",
# #             "version": "1.0.0",
# #             "status": "running"
# #         }

# #     @app.get("/health")
# #     async def health_check():
# #         return {"status": "healthy"}

# #     return app

# # app = create_app()

# # if __name__ == "__main__":
# #     uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)




# # app.py
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from config.database import engine
# from src.models import Base
# from src.api.v1 import categories, products,auth,cart
# import uvicorn
# import os

# # Import all models to ensure they're registered with SQLAlchemy
# from src.models.customer import Customer
# from src.models.otp import OTP

# # Create tables
# Base.metadata.create_all(bind=engine)

# def create_app() -> FastAPI:
#     """Create FastAPI application with all configurations"""
    
#     app = FastAPI(
#         title="E-commerce API with Cart",
#         version="1.0.0",
#         description="A comprehensive e-commerce API with product management and shopping cart functionality"
#     )

#     # CORS middleware
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=["http://localhost:3000", "http://localhost:5173"],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )

#     # Create uploads directory if it doesn't exist
#     os.makedirs("uploads", exist_ok=True)
    
#     # Mount static files for serving uploaded images
#     app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

#     # Include API routers
#     app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
#     app.include_router(categories.router, prefix="/api/v1", tags=["categories"])
#     app.include_router(products.router, prefix="/api/v1", tags=["products"])
#     app.include_router(cart.router, prefix="/api/v1", tags=["cart"])

#     @app.get("/")
#     async def root():
#         return {
#             "message": "E-commerce API",
#             "version": "1.0.0",
#             "status": "running"
#         }

#     @app.get("/health")
#     async def health_check():
#         return {"status": "healthy"}

#     return app

# app = create_app()

# if __name__ == "__main__":
#     uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)



















# Updated app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config.database import engine
from src.models import Base
from src.api.v1 import categories, products, auth,vender_auth, cart, addresses, orders,specifications,pricing
import uvicorn
import os

# Import all models to ensure they're registered with SQLAlchemy
from src.models.customer import Customer
from src.models.otp import OTP
from src.models.address import CustomerAddress
from src.models.order import Order, OrderItem

# Create tables
Base.metadata.create_all(bind=engine)

def create_app() -> FastAPI:
    """Create FastAPI application with all configurations"""
    
    app = FastAPI(
        title="E-commerce API with Cart & Orders",
        version="1.0.0",
        description="A comprehensive e-commerce API with product management, shopping cart, and order functionality"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5174", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create uploads directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    
    # Mount static files for serving uploaded images
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    app.mount("/media", StaticFiles(directory="media"), name="media")

    # Include API routers
    app.include_router(vender_auth.router, prefix="/api/vendor", tags=["vender_auth"])
    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    app.include_router(categories.router, prefix="/api/v1", tags=["categories"])
    app.include_router(specifications.router, prefix="/api/v1", tags=["specifications"])
    app.include_router(pricing.router, prefix="/api/v1", tags=["pricing"])
    app.include_router(products.router, prefix="/api/v1", tags=["products"])
    app.include_router(cart.router, prefix="/api/v1", tags=["cart"])
    app.include_router(addresses.router, prefix="/api/v1", tags=["addresses"])
    app.include_router(orders.router, prefix="/api/v1", tags=["orders"])

    @app.get("/")
    async def root():
        return {
            "message": "E-commerce API with Orders",
            "version": "1.0.0",
            "status": "running",
            "features": ["Authentication", "Products", "Cart", "Addresses", "Orders"]
        }

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
