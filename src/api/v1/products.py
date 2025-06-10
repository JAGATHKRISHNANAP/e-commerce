# src/api/v1/products.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from config.database import get_db
from src.schemas.product import ProductResponse, ProductsListResponse, ProductCreate
from src.services.product_service import ProductService

# Don't forget to add this import at the top of the file
from fastapi import status

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


# Add this to your src/api/v1/products.py file

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    try:
        # Check if category exists
        from src.models.category import Category
        category = db.query(Category).filter(Category.category_id == product_data.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
        
        # Create new product
        from src.models.product import Product
        product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            category_id=product_data.category_id,
            stock_quantity=product_data.stock_quantity,
            image_url=product_data.image_url,
            storage_capacity=product_data.storage_capacity
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        return product
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")
