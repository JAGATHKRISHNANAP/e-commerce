# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.orm import Session
# from typing import List, Optional
# from config.database import get_db
# from src.schemas.product import ProductResponse, ProductsListResponse
# from src.services.product_service import ProductService

# router = APIRouter()

# @router.get("/products", response_model=ProductsListResponse)
# async def get_products(
#     page: int = Query(1, ge=1),
#     per_page: int = Query(20, ge=1, le=100),
#     category_id: Optional[int] = Query(None),
#     search: Optional[str] = Query(None),
#     min_price: Optional[float] = Query(None, ge=0),
#     max_price: Optional[float] = Query(None, ge=0),
#     sort_by: Optional[str] = Query("name", regex="^(name|price|stock_quantity)$"),
#     sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$"),
#     db: Session = Depends(get_db)
# ):
#     """Get products with filtering, searching, and pagination"""
#     service = ProductService(db)
#     products, total_count = service.get_products_with_filters(
#         page, per_page, category_id, search, min_price, max_price, sort_by, sort_order
#     )
    
#     # Calculate total pages
#     total_pages = (total_count + per_page - 1) // per_page
    
#     return ProductsListResponse(
#         products=products,
#         total_count=total_count,
#         page=page,
#         per_page=per_page,
#         total_pages=total_pages
#     )

# @router.get("/products/{product_id}", response_model=ProductResponse)
# async def get_product(product_id: int, db: Session = Depends(get_db)):
#     """Get a single product by ID"""
#     service = ProductService(db)
#     product = service.get_product_by_id(product_id)
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")
#     return product

# @router.get("/products/featured", response_model=List[ProductResponse])
# async def get_featured_products(limit: int = Query(8, ge=1, le=20), db: Session = Depends(get_db)):
#     """Get featured products"""
#     service = ProductService(db)
#     return service.get_featured_products(limit)

# @router.get("/search/suggestions")
# async def get_search_suggestions(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
#     """Get search suggestions"""
#     service = ProductService(db)
#     suggestions = service.get_search_suggestions(q)
#     return suggestions

# @router.get("/price-range")
# async def get_price_range(category_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
#     """Get price range for products"""
#     service = ProductService(db)
#     return service.get_price_range(category_id)




# src/api/v1/products.py - Enhanced with complete CRUD operations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from config.database import get_db
from src.schemas.product import (
    ProductResponse, 
    ProductsListResponse, 
    ProductCreate, 
    ProductUpdate,
    ProductImageCreate,
    ProductImageResponse
)
from src.services.product_service import ProductService
from src.models.product import Product, ProductImage

router = APIRouter()

# ========== EXISTING ENDPOINTS (Your current code) ==========

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
    """Get a single product by ID with JOIN query (your original request)"""
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

# ========== NEW CRUD ENDPOINTS (For your admin UI) ==========

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    try:
        # Check if SKU already exists
        if product_data.sku:
            existing = db.query(Product).filter(Product.sku == product_data.sku).first()
            if existing:
                raise HTTPException(status_code=400, detail="SKU already exists")
        
        # Create product using service
        service = ProductService(db)
        product = service.create_product(product_data)
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, product_data: ProductUpdate, db: Session = Depends(get_db)):
    """Update a product"""
    try:
        service = ProductService(db)
        
        # Check if product exists
        existing_product = service.get_product_by_id(product_id)
        if not existing_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Check SKU uniqueness if changed
        if product_data.sku:
            existing_sku = db.query(Product).filter(
                Product.sku == product_data.sku,
                Product.product_id != product_id
            ).first()
            if existing_sku:
                raise HTTPException(status_code=400, detail="SKU already exists")
        
        # Update product using service
        updated_product = service.update_product(product_id, product_data)
        
        return updated_product
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product"""
    try:
        service = ProductService(db)
        
        # Check if product exists
        product = service.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Delete product using service
        service.delete_product(product_id)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")

# ========== PRODUCT IMAGES ENDPOINTS ==========

@router.post("/products/{product_id}/images", response_model=ProductImageResponse, status_code=status.HTTP_201_CREATED)
async def add_product_image(product_id: int, image_data: ProductImageCreate, db: Session = Depends(get_db)):
    """Add image to product"""
    try:
        # Check if product exists
        service = ProductService(db)
        product = service.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # If this is set as primary, unset other primary images
        if image_data.is_primary:
            db.query(ProductImage).filter(
                ProductImage.product_id == product_id,
                ProductImage.is_primary == True
            ).update({"is_primary": False})
        
        # Create image
        image_dict = image_data.dict(exclude_unset=True)
        image_dict["product_id"] = product_id
        
        image = ProductImage(**image_dict)
        db.add(image)
        db.commit()
        db.refresh(image)
        
        return ProductImageResponse(
            image_id=image.image_id,
            image_url=image.image_url,
            alt_text=image.alt_text,
            is_primary=image.is_primary,
            display_order=image.display_order
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add image: {str(e)}")

@router.get("/products/{product_id}/images", response_model=List[ProductImageResponse])
async def get_product_images(product_id: int, db: Session = Depends(get_db)):
    """Get all images for a product"""
    service = ProductService(db)
    product = service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    images = db.query(ProductImage).filter(
        ProductImage.product_id == product_id
    ).order_by(ProductImage.display_order, ProductImage.is_primary.desc()).all()
    
    return [
        ProductImageResponse(
            image_id=img.image_id,
            image_url=img.image_url,
            alt_text=img.alt_text,
            is_primary=img.is_primary,
            display_order=img.display_order
        ) for img in images
    ]

@router.delete("/products/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_image(product_id: int, image_id: int, db: Session = Depends(get_db)):
    """Delete a product image"""
    try:
        image = db.query(ProductImage).filter(
            ProductImage.image_id == image_id,
            ProductImage.product_id == product_id
        ).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        db.delete(image)
        db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

# ========== ADDITIONAL UTILITY ENDPOINTS ==========

@router.patch("/products/{product_id}/toggle-status")
async def toggle_product_status(product_id: int, db: Session = Depends(get_db)):
    """Toggle product active/inactive status"""
    try:
        product = db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Toggle status
        product.is_active = not product.is_active
        db.commit()
        db.refresh(product)
        
        return {
            "product_id": product_id,
            "name": product.name,
            "is_active": product.is_active,
            "message": f"Product {'activated' if product.is_active else 'deactivated'} successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to toggle product status: {str(e)}")

@router.get("/products/{product_id}/similar")
async def get_similar_products(
    product_id: int, 
    limit: int = Query(5, ge=1, le=20), 
    db: Session = Depends(get_db)
):
    """Get similar products based on category and price range"""
    service = ProductService(db)
    product = service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return service.get_similar_products(product_id, limit)

@router.post("/products/bulk-update-stock")
async def bulk_update_stock(updates: List[dict], db: Session = Depends(get_db)):
    """Bulk update product stock quantities"""
    try:
        updated_count = 0
        errors = []
        
        for update in updates:
            try:
                product_id = update.get("product_id")
                new_stock = update.get("stock_quantity")
                
                if not product_id or new_stock is None:
                    errors.append(f"Invalid data: {update}")
                    continue
                
                product = db.query(Product).filter(Product.product_id == product_id).first()
                if product:
                    product.stock_quantity = new_stock
                    updated_count += 1
                else:
                    errors.append(f"Product {product_id} not found")
                    
            except Exception as e:
                errors.append(f"Error updating product {update.get('product_id', 'unknown')}: {str(e)}")
        
        db.commit()
        
        return {
            "updated_count": updated_count,
            "total_requested": len(updates),
            "errors": errors
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk update failed: {str(e)}")

# ========== ANALYTICS ENDPOINTS ==========

@router.get("/products/analytics/summary")
async def get_products_analytics(db: Session = Depends(get_db)):
    """Get product analytics summary"""
    from sqlalchemy import func
    
    analytics = db.query(
        func.count(Product.product_id).label('total_products'),
        func.count(func.nullif(Product.is_active, False)).label('active_products'),
        func.sum(Product.stock_quantity).label('total_stock'),
        func.avg(Product.price).label('average_price'),
        func.min(Product.price).label('min_price'),
        func.max(Product.price).label('max_price')
    ).first()
    
    return {
        "total_products": analytics.total_products or 0,
        "active_products": analytics.active_products or 0,
        "inactive_products": (analytics.total_products or 0) - (analytics.active_products or 0),
        "total_stock": int(analytics.total_stock or 0),
        "average_price": float(analytics.average_price or 0),
        "min_price": float(analytics.min_price or 0),
        "max_price": float(analytics.max_price or 0)
    }