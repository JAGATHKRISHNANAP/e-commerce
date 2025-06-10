# Project Structure:
# 
# ecommerce_api/
# ├── app.py                    # Main application entry point
# ├── requirements.txt          # Dependencies
# ├── .env                      # Environment variables
# ├── .gitignore               # Git ignore file
# ├── README.md                # Project documentation
# ├── alembic.ini              # Database migration config
# ├── config/
# │   ├── __init__.py
# │   ├── database.py          # Database configuration
# │   └── settings.py          # Application settings
# ├── src/
# │   ├── __init__.py
# │   ├── models/              # SQLAlchemy models
# │   │   ├── __init__.py
# │   │   ├── category.py
# │   │   ├── product.py
# │   │   ├── user.py
# │   │   └── cart.py
# │   ├── schemas/             # Pydantic schemas
# │   │   ├── __init__.py
# │   │   ├── category.py
# │   │   ├── product.py
# │   │   ├── user.py
# │   │   └── cart.py
# │   ├── services/            # Business logic
# │   │   ├── __init__.py
# │   │   ├── category_service.py
# │   │   ├── product_service.py
# │   │   └── cart_service.py
# │   ├── api/                 # API routes
# │   │   ├── __init__.py
# │   │   ├── v1/
# │   │   │   ├── __init__.py
# │   │   │   ├── categories.py
# │   │   │   ├── products.py
# │   │   │   └── cart.py
# │   │   └── deps.py          # Dependencies
# │   └── utils/               # Utility functions
# │       ├── __init__.py
# │       └── helpers.py
# ├── tests/
# │   ├── __init__.py
# │   ├── conftest.py
# │   ├── test_categories.py
# │   ├── test_products.py
# │   └── test_cart.py
# └── alembic/                 # Database migrations
#     └── versions/

# ===========================================
# app.py - Main Application Entry Point
# ===========================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import engine
from src.models import Base
from src.api.v1 import categories, products, cart
import uvicorn

# Create tables
Base.metadata.create_all(bind=engine)

def create_app() -> FastAPI:
    """Create FastAPI application with all configurations"""
    
    app = FastAPI(
        title="E-commerce API with Cart",
        version="1.0.0",
        description="A comprehensive e-commerce API with product management and shopping cart functionality"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    app.include_router(categories.router, prefix="/api/v1", tags=["categories"])
    app.include_router(products.router, prefix="/api/v1", tags=["products"])
    app.include_router(cart.router, prefix="/api/v1", tags=["cart"])

    @app.get("/")
    async def root():
        return {
            "message": "E-commerce API",
            "version": "1.0.0",
            "status": "running"
        }

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

# ===========================================
# config/settings.py - Application Settings
# ===========================================

import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    db_name: str = "datasource"
    db_user: str = "postgres"
    db_password: str = "jaTHU@12"
    db_host: str = "localhost"
    db_port: str = "5432"
    
    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = "E-commerce API"
    
    # CORS
    backend_cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"

settings = Settings()

# ===========================================
# config/database.py - Database Configuration
# ===========================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import urllib.parse
from config.settings import settings

# URL encode the password to handle special characters
encoded_password = urllib.parse.quote_plus(settings.db_password)
DATABASE_URL = f"postgresql://{settings.db_user}:{encoded_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===========================================
# src/models/__init__.py
# ===========================================

from config.database import Base
from .category import Category
from .product import Product
from .user import User
from .cart import CartItem

__all__ = ["Base", "Category", "Product", "User", "CartItem"]

# ===========================================
# src/models/category.py - Category Model
# ===========================================

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from config.database import Base

class Category(Base):
    __tablename__ = "categories"
    
    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    
    products = relationship("Product", back_populates="category")

# ===========================================
# src/models/product.py - Product Model
# ===========================================

from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, Index
from sqlalchemy.orm import relationship
from config.database import Base

class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    stock_quantity = Column(Integer, default=0)
    image_url = Column(Text)
    storage_capacity = Column(String(50))
    
    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")

# Create indexes
Index('idx_products_category_id', Product.category_id)
Index('idx_products_name', Product.name)

# ===========================================
# src/models/user.py - User Model
# ===========================================

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    cart_items = relationship("CartItem", back_populates="user")

# ===========================================
# src/models/cart.py - Cart Model
# ===========================================

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class CartItem(Base):
    __tablename__ = "cart_items"
    
    cart_item_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity = Column(Integer, nullable=False, default=1)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

# Create indexes
Index('idx_cart_items_user_id', CartItem.user_id)
Index('idx_cart_items_product_id', CartItem.product_id)

# ===========================================
# src/schemas/category.py - Category Schemas
# ===========================================

from pydantic import BaseModel

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    category_id: int
    
    class Config:
        from_attributes = True

# ===========================================
# src/schemas/product.py - Product Schemas
# ===========================================

from pydantic import BaseModel
from typing import Optional, List
from .category import CategoryResponse

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category_id: int
    stock_quantity: int = 0
    image_url: Optional[str] = None
    storage_capacity: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    product_id: int
    category: Optional[CategoryResponse] = None
    
    class Config:
        from_attributes = True

class ProductsListResponse(BaseModel):
    products: List[ProductResponse]
    total_count: int
    page: int
    per_page: int
    total_pages: int

# ===========================================
# src/schemas/cart.py - Cart Schemas
# ===========================================

from pydantic import BaseModel
from typing import List
from datetime import datetime
from .product import ProductResponse

class AddToCartRequest(BaseModel):
    session_id: str
    product_id: int
    quantity: int = 1

class UpdateCartRequest(BaseModel):
    session_id: str
    quantity: int

class RemoveFromCartRequest(BaseModel):
    session_id: str

class CartItemResponse(BaseModel):
    cart_item_id: int
    product_id: int
    quantity: int
    added_at: datetime
    product: ProductResponse
    subtotal: float
    
    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_items: int
    total_amount: float

# ===========================================
# src/api/deps.py - Dependencies
# ===========================================

from sqlalchemy.orm import Session
from config.database import get_db
from src.models.user import User

def get_or_create_user(session_id: str, db: Session) -> User:
    """Get or create a user based on session_id"""
    user = db.query(User).filter(User.session_id == session_id).first()
    if not user:
        user = User(session_id=session_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# ===========================================
# src/services/product_service.py - Product Service
# ===========================================

from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.product import Product
from src.models.category import Category
from typing import Optional, Tuple, List

class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def get_products_with_filters(
        self,
        page: int = 1,
        per_page: int = 20,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> Tuple[List[Product], int]:
        """Get products with filtering and pagination"""
        query = self.db.query(Product)
        
        # Apply filters
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        # Apply sorting
        if sort_order == "desc":
            query = query.order_by(getattr(Product, sort_by).desc())
        else:
            query = query.order_by(getattr(Product, sort_by).asc())
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        products = query.offset(offset).limit(per_page).all()
        
        return products, total_count

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get a single product by ID"""
        return self.db.query(Product).filter(Product.product_id == product_id).first()

    def get_featured_products(self, limit: int = 8) -> List[Product]:
        """Get featured products"""
        return self.db.query(Product).filter(Product.stock_quantity > 0).limit(limit).all()

    def get_search_suggestions(self, query: str) -> List[str]:
        """Get search suggestions"""
        suggestions = self.db.query(Product.name).filter(
            Product.name.ilike(f"%{query}%")
        ).distinct().limit(10).all()
        
        return [suggestion[0] for suggestion in suggestions]

    def get_price_range(self, category_id: Optional[int] = None) -> dict:
        """Get price range for products"""
        query = self.db.query(Product)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        result = query.with_entities(
            func.min(Product.price).label('min_price'),
            func.max(Product.price).label('max_price')
        ).first()
        
        return {
            "min_price": float(result.min_price) if result.min_price else 0,
            "max_price": float(result.max_price) if result.max_price else 0
        }

# ===========================================
# src/services/cart_service.py - Cart Service
# ===========================================

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

# ===========================================
# src/api/v1/products.py - Product Routes
# ===========================================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from config.database import get_db
from src.schemas.product import ProductResponse, ProductsListResponse
from src.services.product_service import ProductService

router = APIRouter()

@router.get("/products", response_model=ProductsListResponse)
async def get_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    sort_by: Optional[str] = Query("name", regex="^(name|price|stock_quantity)$"),
    sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """Get products with filtering, searching, and pagination"""
    service = ProductService(db)
    products, total_count = service.get_products_with_filters(
        page, per_page, category_id, search, min_price, max_price, sort_by, sort_order
    )
    
    # Calculate total pages
    total_pages = (total_count + per_page - 1) // per_page
    
    return ProductsListResponse(
        products=products,
        total_count=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID"""
    service = ProductService(db)
    product = service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/products/featured", response_model=List[ProductResponse])
async def get_featured_products(limit: int = Query(8, ge=1, le=20), db: Session = Depends(get_db)):
    """Get featured products"""
    service = ProductService(db)
    return service.get_featured_products(limit)

@router.get("/search/suggestions")
async def get_search_suggestions(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    """Get search suggestions"""
    service = ProductService(db)
    suggestions = service.get_search_suggestions(q)
    return suggestions

@router.get("/price-range")
async def get_price_range(category_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """Get price range for products"""
    service = ProductService(db)
    return service.get_price_range(category_id)

# ===========================================
# src/api/v1/categories.py - Category Routes
# ===========================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from config.database import get_db
from src.models.category import Category
from src.schemas.category import CategoryResponse

router = APIRouter()

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    return db.query(Category).all()

# ===========================================
# src/api/v1/cart.py - Cart Routes
# ===========================================

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

# ===========================================
# src/api/v1/__init__.py
# ===========================================

from . import categories, products, cart

# ===========================================
# requirements.txt
# ===========================================

# fastapi==0.104.1
# uvicorn[standard]==0.24.0
# sqlalchemy==2.0.23
# psycopg2-binary==2.9.9
# pydantic==2.5.0
# python-dotenv==1.0.0
# alembic==1.13.0
# pytest==7.4.3
# pytest-asyncio==0.21.1
# httpx==0.25.2

# ===========================================
# .env (Environment Variables)
# ===========================================

# DB_NAME=datasource
# DB_USER=postgres
# DB_PASSWORD=jaTHU@12
# DB_HOST=localhost
# DB_PORT=5432
# 
# API_V1_STR=/api/v1
# PROJECT_NAME=E-commerce API

# ===========================================
# .gitignore
# ===========================================

# __pycache__/
# *.py[cod]
# *$py.class
# *.so
# .Python
# build/
# develop-eggs/
# dist/
# downloads/
# eggs/
# .eggs/
# lib/
# lib64/
# parts/
# sdist/
# var/
# wheels/
# *.egg-info/
# .installed.cfg
# *.egg
# 
# # Environments
# .env
# .venv
# env/
# venv/
# ENV/
# env.bak/
# venv.bak/
# 
# # Database
# *.db
# *.sqlite3
# 
# # IDE
# .vscode/
# .idea/
# *.swp
# *.swo
# *~
# 
# # Logs
# *.log
# 
# # Alembic
# alembic/versions/*.py
# !alembic/versions/__init__.py

# ===========================================
# Docker Configuration (Optional)
# ===========================================

# Dockerfile
# FROM python:3.11-slim
# 
# WORKDIR /app
# 
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# 
# COPY . .
# 
# EXPOSE 8000
# 
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

# docker-compose.yml
# version: '3.8'
# services:
#   api:
#     build: .
#     ports:
#       - "8000:8000"
#     environment:
#       - DB_HOST=db
#     depends_on:
#       - db
#     volumes:
#       - .:/app
#   
#   db:
#     image: postgres:15
#     environment:
#       POSTGRES_DB: datasource
#       POSTGRES_USER: postgres
#       POSTGRES_PASSWORD: jaTHU@12
#     ports:
#       - "5432:5432"
#     volumes:
#       - postgres_data:/var/lib/postgresql/data
# 
# volumes:
#   postgres_data:

# ===========================================
# Additional Service Examples
# ===========================================

# src/services/auth_service.py - Authentication Service
# from datetime import datetime, timedelta
# from jose import JWTError, jwt
# from passlib.context import CryptContext
# 
# class AuthService:
#     def __init__(self):
#         self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#         self.secret_key = "your-secret-key"
#         self.algorithm = "HS256"
#         self.access_token_expire_minutes = 30
# 
#     def verify_password(self, plain_password, hashed_password):
#         return self.pwd_context.verify(plain_password, hashed_password)
# 
#     def get_password_hash(self, password):
#         return self.pwd_context.hash(password)
# 
#     def create_access_token(self, data: dict):
#         to_encode = data.copy()
#         expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
#         to_encode.update({"exp": expire})
#         encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
#         return encoded_jwt

# src/services/order_service.py - Order Management Service
# from sqlalchemy.orm import Session
# from src.models.order import Order, OrderItem
# from src.services.cart_service import CartService
# 
# class OrderService:
#     def __init__(self, db: Session):
#         self.db = db
#         self.cart_service = CartService(db)
# 
#     def create_order_from_cart(self, session_id: str, shipping_address: dict):
#         """Create order from cart items"""
#         cart = self.cart_service.get_cart(session_id)
#         
#         if not cart["items"]:
#             raise ValueError("Cart is empty")
#         
#         # Create order logic here
#         # ...
#         
#         return {"order_id": "new_order_id", "status": "created"}

# src/middleware/logging.py - Request Logging Middleware
# import time
# import logging
# from fastapi import Request
# from starlette.middleware.base import BaseHTTPMiddleware
# 
# logger = logging.getLogger(__name__)
# 
# class LoggingMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         start_time = time.time()
#         
#         response = await call_next(request)
#         
#         process_time = time.time() - start_time
#         logger.info(
#             f"{request.method} {request.url.path} - "
#             f"Status: {response.status_code} - "
#             f"Time: {process_time:.4f}s"
#         )
#         
#         return response

# ===========================================
# Testing Examples
# ===========================================

# tests/conftest.py - Test Configuration
# import pytest
# from fastapi.testclient import TestClient
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from config.database import get_db, Base
# from app import app
# 
# SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
# 
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# 
# Base.metadata.create_all(bind=engine)
# 
# def override_get_db():
#     try:
#         db = TestingSessionLocal()
#         yield db
#     finally:
#         db.close()
# 
# app.dependency_overrides[get_db] = override_get_db
# 
# @pytest.fixture
# def client():
#     return TestClient(app)

# tests/test_products.py - Product Tests
# def test_get_products(client):
#     response = client.get("/api/v1/products")
#     assert response.status_code == 200
#     data = response.json()
#     assert "products" in data
#     assert "total_count" in data
# 
# def test_get_product_by_id(client):
#     # Assuming product with ID 1 exists
#     response = client.get("/api/v1/products/1")
#     assert response.status_code in [200, 404]

# ===========================================
# Performance & Production Considerations
# ===========================================

# src/utils/cache.py - Redis Caching
# import redis
# import json
# from typing import Optional, Any
# 
# class CacheService:
#     def __init__(self, redis_url: str = "redis://localhost:6379"):
#         self.redis_client = redis.from_url(redis_url)
# 
#     def get(self, key: str) -> Optional[Any]:
#         value = self.redis_client.get(key)
#         return json.loads(value) if value else None
# 
#     def set(self, key: str, value: Any, expire: int = 3600):
#         self.redis_client.set(key, json.dumps(value), ex=expire)
# 
#     def delete(self, key: str):
#         self.redis_client.delete(key)

# src/utils/pagination.py - Advanced Pagination
# from typing import Generic, TypeVar, List
# from pydantic import BaseModel
# from fastapi import Query
# 
# T = TypeVar('T')
# 
# class PaginatedResponse(BaseModel, Generic[T]):
#     items: List[T]
#     total: int
#     page: int
#     per_page: int
#     pages: int
#     has_next: bool
#     has_prev: bool
# 
# class PaginationParams:
#     def __init__(
#         self,
#         page: int = Query(1, ge=1, description="Page number"),
#         per_page: int = Query(20, ge=1, le=100, description="Items per page")
#     ):
#         self.page = page
#         self.per_page = per_page
#         self.offset = (page - 1) * per_page