# src/api/v1/products.py - Updated with working price and sort filters
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, func
from typing import List, Optional
from config.database import get_db
from src.models.category import Category, Subcategory
from src.models.product import Product
from src.models.product_image import ProductImage
from src.schemas.product import ProductResponse, ProductListResponse
from src.services.pricing_service import PricingService
from src.services.file_service import FileService
from src.services.product_service import ProductService
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Your existing create_product endpoint remains unchanged
@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    # Form data - make some fields optional with defaults
    name: str = Form(...),
    description: str = Form(""),  # Default empty string instead of Optional
    category_id: int = Form(...),
    subcategory_id: int = Form(...),
    specifications: str = Form("{}"),  # JSON string
    base_price: str = Form(...),  # Accept as string to handle conversion
    stock_quantity: str = Form("0"),  # Accept as string to handle conversion
    sku: str = Form(""),  # Default empty string
    created_by: str = Form("admin"),
    is_active: str = Form("true"),  # Accept as string
    
    # File uploads - make optional
    images: List[UploadFile] = File(default=[]),
    
    # Dependencies
    db: Session = Depends(get_db)
):
    # Your existing create_product implementation stays the same
    pass  # Replace with your existing implementation

# UPDATED: Enhanced get_products endpoint with proper price and sort filtering
@router.get("/products", response_model=ProductListResponse)
async def get_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    category_id: Optional[int] = Query(None, description="Category ID (integer)"),
    subcategory_id: Optional[int] = Query(None, description="Subcategory ID (integer)"),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("name", description="Sort field: name, price, created_at"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    min_price: Optional[float] = Query(None, description="Minimum price in rupees"),
    max_price: Optional[float] = Query(None, description="Maximum price in rupees"),
    db: Session = Depends(get_db)
):
    """Get products with pagination and enhanced filters including price and sorting"""
    try:
        logger.info(f"Product search - Category: {category_id}, Subcategory: {subcategory_id}")
        logger.info(f"Price range: {min_price} - {max_price}")
        logger.info(f"Sort: {sort_by} {sort_order}")
        
        query = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.subcategory),
            joinedload(Product.images)
        )
        
        # Apply filters with validation
        if category_id is not None and category_id > 0:
            query = query.filter(Product.category_id == category_id)
            logger.info(f"Applied category filter: {category_id}")
            
        if subcategory_id is not None and subcategory_id > 0:
            query = query.filter(Product.subcategory_id == subcategory_id)
            logger.info(f"Applied subcategory filter: {subcategory_id}")
            
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        else:
            # By default, only show active products
            query = query.filter(Product.is_active == True)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(Product.name.ilike(search_term))
            logger.info(f"Applied search filter: {search}")
        
        # PRICE FILTERING - Convert rupees to cents for database comparison
        if min_price is not None:
            min_price_cents = int(min_price * 100)  # Convert rupees to cents
            query = query.filter(
                func.coalesce(Product.calculated_price, Product.base_price) >= min_price_cents
            )
            logger.info(f"Applied min price filter: ₹{min_price} ({min_price_cents} cents)")
            
        if max_price is not None:
            max_price_cents = int(max_price * 100)  # Convert rupees to cents
            query = query.filter(
                func.coalesce(Product.calculated_price, Product.base_price) <= max_price_cents
            )
            logger.info(f"Applied max price filter: ₹{max_price} ({max_price_cents} cents)")
        
        # SORTING
        if sort_by == "price":
            # Sort by calculated_price if available, otherwise base_price
            price_column = func.coalesce(Product.calculated_price, Product.base_price)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(price_column))
            else:
                query = query.order_by(asc(price_column))
            logger.info(f"Applied price sorting: {sort_order}")
            
        elif sort_by == "created_at":
            if sort_order.lower() == "desc":
                query = query.order_by(desc(Product.created_at))
            else:
                query = query.order_by(asc(Product.created_at))
            logger.info(f"Applied date sorting: {sort_order}")
            
        elif sort_by == "name":
            if sort_order.lower() == "desc":
                query = query.order_by(desc(Product.name))
            else:
                query = query.order_by(asc(Product.name))
            logger.info(f"Applied name sorting: {sort_order}")
        else:
            # Default sorting by name ascending
            query = query.order_by(asc(Product.name))
            logger.info("Applied default name sorting")
        
        # Get total count before pagination
        total_count = query.count()
        logger.info(f"Total products found: {total_count}")
        
        # Apply pagination
        offset = (page - 1) * per_page
        products = query.offset(offset).limit(per_page).all()
        
        # Convert products to response format
        product_responses = []
        for product in products:
            # Calculate display price (convert cents to rupees)
            display_price = (product.calculated_price or product.base_price or 0) / 100
            
            response_data = {
                "product_id": product.product_id,
                "name": product.name,
                "description": product.description,
                "category_id": product.category_id,
                "subcategory_id": product.subcategory_id,
                "specifications": product.specifications,
                "base_price": product.base_price,
                "calculated_price": product.calculated_price,
                "stock_quantity": product.stock_quantity,
                "sku": product.sku,
                "is_active": product.is_active,
                "created_by": product.created_by,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
                "category": {
                    "category_id": product.category.category_id,
                    "name": product.category.name,
                    "description": product.category.description
                } if product.category else None,
                "subcategory": {
                    "subcategory_id": product.subcategory.subcategory_id,
                    "name": product.subcategory.name,
                    "description": product.subcategory.description
                } if product.subcategory else None,
                "primary_image_url": product.primary_image_url,
                "primary_image_filename": product.primary_image_filename
            }
            product_responses.append(ProductResponse(**response_data))
        
        total_pages = (total_count + per_page - 1) // per_page
        
        logger.info(f"Returning {len(product_responses)} products, page {page}/{total_pages}")
        
        return ProductListResponse(
            products=product_responses,
            total_count=total_count,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except ValueError as e:
        logger.error(f"Invalid parameter: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Error in get_products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# NEW: Add endpoint to get price range for filter component
@router.get("/price-range")
async def get_price_range(
    category_id: Optional[int] = Query(None),
    subcategory_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get the min and max price range for products (for price filter component)"""
    try:
        query = db.query(Product).filter(Product.is_active == True)
        
        # Apply category/subcategory filters if provided
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if subcategory_id:
            query = query.filter(Product.subcategory_id == subcategory_id)
        
        # Get min and max prices using coalesce to handle both calculated_price and base_price
        price_column = func.coalesce(Product.calculated_price, Product.base_price)
        
        result = query.with_entities(
            func.min(price_column).label('min_price'),
            func.max(price_column).label('max_price')
        ).first()
        
        # Convert from cents to rupees
        min_price = (result.min_price or 0) / 100
        max_price = (result.max_price or 10000) / 100  # Default max if no products
        
        logger.info(f"Price range: ₹{min_price} - ₹{max_price}")
        
        return {
            "min_price": min_price,
            "max_price": max_price,
            "currency": "INR"
        }
        
    except Exception as e:
        logger.error(f"Error getting price range: {e}")
        return {
            "min_price": 0,
            "max_price": 10000,
            "currency": "INR"
        }


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID"""
    service = ProductService(db)
    product = service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Your existing test endpoint remains unchanged
@router.post("/products/test")
async def test_form_data(
    name: str = Form(...),
    category_id: int = Form(...),
    base_price: str = Form(...),
    images: List[UploadFile] = File(default=[])
):
    """Test endpoint to debug form data"""
    return {
        "name": name,
        "category_id": category_id,
        "base_price": base_price,
        "images_count": len(images),
        "image_names": [img.filename for img in images if img.filename]
    }