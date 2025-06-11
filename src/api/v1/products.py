# # src/api/v1/products.py
# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.orm import Session
# from typing import List, Optional
# from config.database import get_db
# from src.schemas.product import ProductResponse, ProductsListResponse, ProductCreate
# from src.services.product_service import ProductService

# # Don't forget to add this import at the top of the file
# from fastapi import status

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


# # Add this to your src/api/v1/products.py file

# @router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
# async def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
#     """Create a new product"""
#     try:
#         # Check if category exists
#         from src.models.category import Category
#         category = db.query(Category).filter(Category.category_id == product_data.category_id).first()
#         if not category:
#             raise HTTPException(status_code=400, detail="Category not found")
        
#         # Create new product
#         from src.models.product import Product
#         product = Product(
#             name=product_data.name,
#             description=product_data.description,
#             price=product_data.price,
#             category_id=product_data.category_id,
#             stock_quantity=product_data.stock_quantity,
#             image_url=product_data.image_url,
#             storage_capacity=product_data.storage_capacity
#         )
        
#         db.add(product)
#         db.commit()
#         db.refresh(product)
        
#         return product
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")
















# # src/api/v1/products.py - Updated with file upload capabilities
# from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
# from sqlalchemy.orm import Session
# from typing import List, Optional
# from config.database import get_db
# from src.schemas.product import ProductResponse, ProductsListResponse, ProductCreateWithImages
# from src.services.product_service import ProductService
# from src.services.file_service import FileService
# from src.models.product import Product
# from src.models.product_image import ProductImage
# from src.models.category import Category
# from fastapi import status

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

# @router.post("/products", status_code=status.HTTP_201_CREATED)
# async def create_product_with_images(
#     name: str = Form(...),
#     description: Optional[str] = Form(None),
#     price: float = Form(...),
#     category_id: int = Form(...),
#     stock_quantity: int = Form(0),
#     storage_capacity: Optional[str] = Form(None),
#     sales_user: str = Form(...),  # Sales user identifier
#     images: List[UploadFile] = File(...),  # Multiple image uploads
#     db: Session = Depends(get_db)
# ):
#     """Create a new product with image uploads"""
    
#     file_service = FileService()
    
#     try:
#         # Validate category exists
#         category = db.query(Category).filter(Category.category_id == category_id).first()
#         if not category:
#             raise HTTPException(status_code=400, detail="Category not found")
        
#         # Validate price
#         if price <= 0:
#             raise HTTPException(status_code=400, detail="Price must be greater than 0")
        
#         # Create product first
#         product = Product(
#             name=name,
#             description=description,
#             price=price,
#             category_id=category_id,
#             stock_quantity=stock_quantity,
#             storage_capacity=storage_capacity,
#             created_by=sales_user
#         )
        
#         db.add(product)
#         db.commit()
#         db.refresh(product)
        
#         # Upload and save images
#         upload_results = await file_service.save_multiple_product_images(
#             images, sales_user, product.product_id
#         )
        
#         # Save image records to database
#         saved_images = []
#         for i, file_info in enumerate(upload_results["saved_files"]):
#             product_image = ProductImage(
#                 product_id=product.product_id,
#                 image_filename=file_info["filename"],
#                 image_path=file_info["file_path"],
#                 image_url=file_info["image_url"],
#                 alt_text=f"{product.name} - Image {i+1}",
#                 is_primary=(i == 0),  # First image is primary
#                 display_order=i + 1,
#                 uploaded_by=sales_user,
#                 file_size=file_info["file_size"],
#                 mime_type=file_info["mime_type"]
#             )
#             db.add(product_image)
#             saved_images.append(product_image)
        
#         db.commit()
        
#         # Refresh to get relationships
#         db.refresh(product)
        
#         return {
#             "message": "Product created successfully",
#             "product": {
#                 "product_id": product.product_id,
#                 "name": product.name,
#                 "description": product.description,
#                 "price": float(product.price),
#                 "category_id": product.category_id,
#                 "stock_quantity": product.stock_quantity,
#                 "storage_capacity": product.storage_capacity,
#                 "created_by": product.created_by,
#                 "category": {
#                     "category_id": category.category_id,
#                     "name": category.name
#                 }
#             },
#             "images": [
#                 {
#                     "image_id": img.image_id,
#                     "image_url": img.image_url,
#                     "is_primary": img.is_primary,
#                     "display_order": img.display_order,
#                     "filename": img.image_filename,
#                     "file_size": img.file_size
#                 } for img in saved_images
#             ],
#             "upload_summary": {
#                 "total_uploaded": upload_results["total_uploaded"],
#                 "total_failed": upload_results["total_failed"],
#                 "failed_files": upload_results["failed_files"]
#             }
#         }
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

# @router.post("/products/{product_id}/images", status_code=status.HTTP_201_CREATED)
# async def add_product_images(
#     product_id: int,
#     sales_user: str = Form(...),
#     images: List[UploadFile] = File(...),
#     db: Session = Depends(get_db)
# ):
#     """Add additional images to existing product"""
    
#     file_service = FileService()
    
#     try:
#         # Check if product exists and user has permission
#         product = db.query(Product).filter(Product.product_id == product_id).first()
#         if not product:
#             raise HTTPException(status_code=404, detail="Product not found")
        
#         # Optional: Check if sales_user owns the product
#         if product.created_by != sales_user:
#             raise HTTPException(status_code=403, detail="Not authorized to add images to this product")
        
#         # Get current image count for display order
#         current_count = db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
        
#         # Upload images
#         upload_results = await file_service.save_multiple_product_images(
#             images, sales_user, product_id
#         )
        
#         # Save image records
#         saved_images = []
#         for i, file_info in enumerate(upload_results["saved_files"]):
#             product_image = ProductImage(
#                 product_id=product_id,
#                 image_filename=file_info["filename"],
#                 image_path=file_info["file_path"],
#                 image_url=file_info["image_url"],
#                 alt_text=f"{product.name} - Image {current_count + i + 1}",
#                 is_primary=False,  # Additional images are not primary
#                 display_order=current_count + i + 1,
#                 uploaded_by=sales_user,
#                 file_size=file_info["file_size"],
#                 mime_type=file_info["mime_type"]
#             )
#             db.add(product_image)
#             saved_images.append(product_image)
        
#         db.commit()
        
#         return {
#             "message": f"Added {len(saved_images)} images to product",
#             "product_id": product_id,
#             "images": [
#                 {
#                     "image_id": img.image_id,
#                     "image_url": img.image_url,
#                     "display_order": img.display_order,
#                     "filename": img.image_filename,
#                     "file_size": img.file_size
#                 } for img in saved_images
#             ],
#             "upload_summary": upload_results
#         }
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to add images: {str(e)}")

# @router.get("/products/{product_id}/images")
# async def get_product_images(product_id: int, db: Session = Depends(get_db)):
#     """Get all images for a product"""
    
#     product = db.query(Product).filter(Product.product_id == product_id).first()
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     images = db.query(ProductImage).filter(
#         ProductImage.product_id == product_id
#     ).order_by(ProductImage.display_order).all()
    
#     return {
#         "product_id": product_id,
#         "product_name": product.name,
#         "total_images": len(images),
#         "images": [
#             {
#                 "image_id": img.image_id,
#                 "image_url": img.image_url,
#                 "alt_text": img.alt_text,
#                 "is_primary": img.is_primary,
#                 "display_order": img.display_order,
#                 "filename": img.image_filename,
#                 "file_size": img.file_size,
#                 "mime_type": img.mime_type,
#                 "uploaded_by": img.uploaded_by,
#                 "created_at": img.created_at
#             } for img in images
#         ]
#     }

# @router.delete("/images/{image_id}")
# async def delete_product_image(image_id: int, sales_user: str = Query(...), db: Session = Depends(get_db)):
#     """Delete a product image"""
    
#     file_service = FileService()
    
#     try:
#         image = db.query(ProductImage).filter(ProductImage.image_id == image_id).first()
#         if not image:
#             raise HTTPException(status_code=404, detail="Image not found")
        
#         # Check permission
#         if image.uploaded_by != sales_user:
#             raise HTTPException(status_code=403, detail="Not authorized to delete this image")
        
#         # Delete file from filesystem
#         file_service.delete_file(image.image_path)
        
#         # Delete from database
#         db.delete(image)
#         db.commit()
        
#         return {"message": "Image deleted successfully", "image_id": image_id}
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

# @router.get("/storage/user/{sales_user}")
# async def get_user_storage_info(sales_user: str):
#     """Get storage information for a sales user"""
#     file_service = FileService()
#     return file_service.get_user_storage_info(sales_user)

# # Keep existing endpoints
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





















# src/api/v1/products.py - Fixed imports
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from config.database import get_db
from src.schemas.product import ProductResponse, ProductsListResponse, ProductCreate
from src.schemas.product_image import ProductImageResponse, ProductImageListResponse
from src.services.product_service import ProductService
from src.services.file_service import FileService
from src.models.product import Product
from src.models.product_image import ProductImage
from src.models.category import Category
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

@router.post("/products", status_code=status.HTTP_201_CREATED)
async def create_product_with_images(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    category_id: int = Form(...),
    stock_quantity: int = Form(0),
    storage_capacity: Optional[str] = Form(None),
    sales_user: str = Form(...),  # Sales user identifier
    images: List[UploadFile] = File(...),  # Multiple image uploads
    db: Session = Depends(get_db)
):
    """Create a new product with image uploads"""
    
    file_service = FileService()
    
    try:
        # Validate category exists
        category = db.query(Category).filter(Category.category_id == category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
        
        # Validate price
        if price <= 0:
            raise HTTPException(status_code=400, detail="Price must be greater than 0")
        
        # Create product first
        product = Product(
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            stock_quantity=stock_quantity,
            storage_capacity=storage_capacity,
            created_by=sales_user
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        # Upload and save images
        upload_results = await file_service.save_multiple_product_images(
            images, sales_user, product.product_id
        )
        
        # Save image records to database
        saved_images = []
        for i, file_info in enumerate(upload_results["saved_files"]):
            product_image = ProductImage(
                product_id=product.product_id,
                image_filename=file_info["filename"],
                image_path=file_info["file_path"],
                image_url=file_info["image_url"],
                alt_text=f"{product.name} - Image {i+1}",
                is_primary=(i == 0),  # First image is primary
                display_order=i + 1,
                uploaded_by=sales_user,
                file_size=file_info["file_size"],
                mime_type=file_info["mime_type"]
            )
            db.add(product_image)
            saved_images.append(product_image)
        
        db.commit()
        
        # Refresh to get relationships
        db.refresh(product)
        
        return {
            "message": "Product created successfully",
            "product": {
                "product_id": product.product_id,
                "name": product.name,
                "description": product.description,
                "price": float(product.price),
                "category_id": product.category_id,
                "stock_quantity": product.stock_quantity,
                "storage_capacity": product.storage_capacity,
                "created_by": product.created_by,
                "category": {
                    "category_id": category.category_id,
                    "name": category.name
                }
            },
            "images": [
                {
                    "image_id": img.image_id,
                    "image_url": img.image_url,
                    "is_primary": img.is_primary,
                    "display_order": img.display_order,
                    "filename": img.image_filename,
                    "file_size": img.file_size
                } for img in saved_images
            ],
            "upload_summary": {
                "total_uploaded": upload_results["total_uploaded"],
                "total_failed": upload_results["total_failed"],
                "failed_files": upload_results["failed_files"]
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

@router.post("/products/{product_id}/images", status_code=status.HTTP_201_CREATED)
async def add_product_images(
    product_id: int,
    sales_user: str = Form(...),
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Add additional images to existing product"""
    
    file_service = FileService()
    
    try:
        # Check if product exists and user has permission
        product = db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Optional: Check if sales_user owns the product
        if product.created_by != sales_user:
            raise HTTPException(status_code=403, detail="Not authorized to add images to this product")
        
        # Get current image count for display order
        current_count = db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
        
        # Upload images
        upload_results = await file_service.save_multiple_product_images(
            images, sales_user, product_id
        )
        
        # Save image records
        saved_images = []
        for i, file_info in enumerate(upload_results["saved_files"]):
            product_image = ProductImage(
                product_id=product_id,
                image_filename=file_info["filename"],
                image_path=file_info["file_path"],
                image_url=file_info["image_url"],
                alt_text=f"{product.name} - Image {current_count + i + 1}",
                is_primary=False,  # Additional images are not primary
                display_order=current_count + i + 1,
                uploaded_by=sales_user,
                file_size=file_info["file_size"],
                mime_type=file_info["mime_type"]
            )
            db.add(product_image)
            saved_images.append(product_image)
        
        db.commit()
        
        return {
            "message": f"Added {len(saved_images)} images to product",
            "product_id": product_id,
            "images": [
                {
                    "image_id": img.image_id,
                    "image_url": img.image_url,
                    "display_order": img.display_order,
                    "filename": img.image_filename,
                    "file_size": img.file_size
                } for img in saved_images
            ],
            "upload_summary": upload_results
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add images: {str(e)}")

@router.get("/products/{product_id}/images", response_model=ProductImageListResponse)
async def get_product_images(product_id: int, db: Session = Depends(get_db)):
    """Get all images for a product"""
    
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    images = db.query(ProductImage).filter(
        ProductImage.product_id == product_id
    ).order_by(ProductImage.display_order).all()
    
    return ProductImageListResponse(
        product_id=product_id,
        product_name=product.name,
        total_images=len(images),
        images=images
    )

# Keep your existing endpoints for backwards compatibility
@router.get("/products/featured")
async def get_featured_products(limit: int = Query(8, ge=1, le=20), db: Session = Depends(get_db)):
    """Get featured products"""
    # Simple implementation - you can enhance this based on your needs
    products = db.query(Product).limit(limit).all()
    return [
        {
            "product_id": p.product_id,
            "name": p.name,
            "price": float(p.price),
            "stock_quantity": p.stock_quantity
        } for p in products
    ]

@router.get("/search/suggestions")
async def get_search_suggestions(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    """Get search suggestions"""
    products = db.query(Product).filter(Product.name.ilike(f"%{q}%")).limit(5).all()
    return {
        "suggestions": [p.name for p in products]
    }

@router.get("/price-range")
async def get_price_range(category_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """Get price range for products"""
    query = db.query(Product)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    products = query.all()
    if not products:
        return {"min_price": 0, "max_price": 0}
    
    prices = [float(p.price) for p in products]
    return {
        "min_price": min(prices),
        "max_price": max(prices)
    }