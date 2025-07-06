# # src/api/v1/products.py - Fixed imports
# from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
# from sqlalchemy.orm import Session
# from typing import List, Optional
# from config.database import get_db
# from src.schemas.product import ProductResponse, ProductsListResponse, ProductCreate
# from src.schemas.product_image import ProductImageResponse, ProductImageListResponse
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
#         primary_image_set = False
        
#         for i, file_info in enumerate(upload_results["saved_files"]):
#             is_primary = (i == 0)  # First image is primary
            
#             product_image = ProductImage(
#                 product_id=product.product_id,
#                 image_filename=file_info["filename"],
#                 image_path=file_info["file_path"],
#                 image_url=file_info["image_url"],
#                 alt_text=f"{product.name} - Image {i+1}",
#                 is_primary=is_primary,
#                 display_order=i + 1,
#                 uploaded_by=sales_user,
#                 file_size=file_info["file_size"],
#                 mime_type=file_info["mime_type"]
#             )
#             db.add(product_image)
#             saved_images.append(product_image)
            
#             # Set primary image in product table for quick access
#             if is_primary and not primary_image_set:
#                 product.primary_image_url = file_info["image_url"]
#                 product.primary_image_filename = file_info["filename"]
#                 primary_image_set = True
        
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

# @router.get("/products/{product_id}/images", response_model=ProductImageListResponse)
# async def get_product_images(product_id: int, db: Session = Depends(get_db)):
#     """Get all images for a product"""
    
#     product = db.query(Product).filter(Product.product_id == product_id).first()
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     images = db.query(ProductImage).filter(
#         ProductImage.product_id == product_id
#     ).order_by(ProductImage.display_order).all()
    
#     return ProductImageListResponse(
#         product_id=product_id,
#         product_name=product.name,
#         total_images=len(images),
#         images=images
#     )

# # Keep your existing endpoints for backwards compatibility
# @router.get("/products/featured")
# async def get_featured_products(limit: int = Query(8, ge=1, le=20), db: Session = Depends(get_db)):
#     """Get featured products"""
#     # Simple implementation - you can enhance this based on your needs
#     products = db.query(Product).limit(limit).all()
#     return [
#         {
#             "product_id": p.product_id,
#             "name": p.name,
#             "price": float(p.price),
#             "stock_quantity": p.stock_quantity
#         } for p in products
#     ]

# @router.get("/search/suggestions")
# async def get_search_suggestions(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
#     """Get search suggestions"""
#     products = db.query(Product).filter(Product.name.ilike(f"%{q}%")).limit(5).all()
#     return {
#         "suggestions": [p.name for p in products]
#     }

# @router.get("/price-range")
# async def get_price_range(category_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
#     """Get price range for products"""
#     query = db.query(Product)
#     if category_id:
#         query = query.filter(Product.category_id == category_id)
    
#     products = query.all()
#     if not products:
#         return {"min_price": 0, "max_price": 0}
    
#     prices = [float(p.price) for p in products]
#     return {
#         "min_price": min(prices),
#         "max_price": max(prices)
#     }


# @router.patch("/products/{product_id}/primary-image/{image_id}")
# async def set_primary_image(
#     product_id: int, 
#     image_id: int, 
#     sales_user: str = Query(...), 
#     db: Session = Depends(get_db)
# ):
#     """Set a specific image as the primary image for a product"""
#     try:
#         # Check if product exists and user has permission
#         product = db.query(Product).filter(Product.product_id == product_id).first()
#         if not product:
#             raise HTTPException(status_code=404, detail="Product not found")
        
#         if product.created_by != sales_user:
#             raise HTTPException(status_code=403, detail="Not authorized to modify this product")
        
#         # Check if image exists and belongs to this product
#         new_primary_image = db.query(ProductImage).filter(
#             ProductImage.image_id == image_id,
#             ProductImage.product_id == product_id
#         ).first()
        
#         if not new_primary_image:
#             raise HTTPException(status_code=404, detail="Image not found for this product")
        
#         # Update all images to not be primary
#         db.query(ProductImage).filter(ProductImage.product_id == product_id).update(
#             {"is_primary": False}
#         )
        
#         # Set the new primary image
#         new_primary_image.is_primary = True
        
#         # Update the product's primary image references
#         product.primary_image_url = new_primary_image.image_url
#         product.primary_image_filename = new_primary_image.image_filename
        
#         db.commit()
        
#         return {
#             "message": "Primary image updated successfully",
#             "product_id": product_id,
#             "new_primary_image": {
#                 "image_id": new_primary_image.image_id,
#                 "image_url": new_primary_image.image_url,
#                 "filename": new_primary_image.image_filename
#             }
#         }
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to set primary image: {str(e)}")

# @router.get("/products/{product_id}/primary-image")
# async def get_primary_image(product_id: int, db: Session = Depends(get_db)):
#     """Get the primary image for a product"""
#     product = db.query(Product).filter(Product.product_id == product_id).first()
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     if not product.primary_image_url:
#         raise HTTPException(status_code=404, detail="No primary image set for this product")
    
#     return {
#         "product_id": product_id,
#         "product_name": product.name,
#         "primary_image": {
#             "image_url": product.primary_image_url,
#             "filename": product.primary_image_filename
#         }
#     }

# @router.delete("/images/{image_id}")
# async def delete_product_image(image_id: int, sales_user: str = Query(...), db: Session = Depends(get_db)):
#     """Delete a product image and update primary image if necessary"""
    
#     file_service = FileService()
    
#     try:
#         image = db.query(ProductImage).filter(ProductImage.image_id == image_id).first()
#         if not image:
#             raise HTTPException(status_code=404, detail="Image not found")
        
#         # Check permission
#         if image.uploaded_by != sales_user:
#             raise HTTPException(status_code=403, detail="Not authorized to delete this image")
        
#         product_id = image.product_id
#         was_primary = image.is_primary
        
#         # Get the product
#         product = db.query(Product).filter(Product.product_id == product_id).first()
        
#         # Delete file from filesystem
#         file_service.delete_file(image.image_path)
        
#         # Delete from database
#         db.delete(image)
        
#         # If this was the primary image, set a new primary image
#         if was_primary:
#             # Find the next image to make primary (lowest display_order)
#             next_primary = db.query(ProductImage).filter(
#                 ProductImage.product_id == product_id,
#                 ProductImage.image_id != image_id
#             ).order_by(ProductImage.display_order).first()
            
#             if next_primary:
#                 # Set new primary image
#                 next_primary.is_primary = True
#                 product.primary_image_url = next_primary.image_url
#                 product.primary_image_filename = next_primary.image_filename
#             else:
#                 # No more images, clear primary image from product
#                 product.primary_image_url = None
#                 product.primary_image_filename = None
        
#         db.commit()
        
#         return {
#             "message": "Image deleted successfully",
#             "image_id": image_id,
#             "was_primary": was_primary,
#             "new_primary_set": was_primary and next_primary is not None if 'next_primary' in locals() else False
#         }
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

# # Enhanced product listing with quick image access
# @router.get("/products/quick-list")
# async def get_products_quick_list(
#     page: int = Query(1, ge=1),
#     per_page: int = Query(20, ge=1, le=100),
#     category_id: Optional[int] = Query(None),
#     search: Optional[str] = Query(None),
#     db: Session = Depends(get_db)
# ):
#     """Get products with primary images for quick listing (no need to join images table)"""
    
#     query = db.query(Product)
    
#     if category_id:
#         query = query.filter(Product.category_id == category_id)
    
#     if search:
#         query = query.filter(Product.name.ilike(f"%{search}%"))
    
#     # Get total count
#     total_count = query.count()
    
#     # Get paginated results
#     products = query.offset((page - 1) * per_page).limit(per_page).all()
    
#     # Calculate total pages
#     total_pages = (total_count + per_page - 1) // per_page
    
#     return {
#         "products": [
#             {
#                 "product_id": p.product_id,
#                 "name": p.name,
#                 "price": float(p.price),
#                 "stock_quantity": p.stock_quantity,
#                 "primary_image_url": p.primary_image_url,
#                 "primary_image_filename": p.primary_image_filename,
#                 "created_by": p.created_by
#             } for p in products
#         ],
#         "total_count": total_count,
#         "page": page,
#         "per_page": per_page,
#         "total_pages": total_pages
#     }





# # src/api/v1/products.py - Updated for dynamic specifications
# from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
# from sqlalchemy.orm import Session, joinedload
# from typing import List, Optional, Dict, Any
# from config.database import get_db
# from src.schemas.product import (
#     ProductResponse, ProductListResponse, ProductCreate, ProductUpdate,
#     PriceCalculationRequest, PriceCalculationResponse
# )
# from src.models.product import Product
# from src.models.category import Category, Subcategory
# from src.services.pricing_service import PricingService
# from src.services.file_service import FileService
# import json

# router = APIRouter()

# @router.get("/products", response_model=ProductListResponse)
# async def get_products(
#     page: int = Query(1, ge=1),
#     per_page: int = Query(20, ge=1, le=100),
#     category_id: Optional[int] = Query(None),
#     subcategory_id: Optional[int] = Query(None),
#     search: Optional[str] = Query(None),
#     min_price: Optional[float] = Query(None, ge=0),
#     max_price: Optional[float] = Query(None, ge=0),
#     specifications: Optional[str] = Query(None, description="JSON string of spec filters"),
#     sort_by: Optional[str] = Query("name", regex="^(name|calculated_price|created_at|stock_quantity)$"),
#     sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$"),
#     is_active: Optional[bool] = Query(None),
#     db: Session = Depends(get_db)
# ):
#     """Get products with advanced filtering"""
#     try:
#         # Build query with relationships
#         query = db.query(Product).options(
#             joinedload(Product.category),
#             joinedload(Product.subcategory)
#         )
        
#         # Apply filters
#         if category_id:
#             query = query.filter(Product.category_id == category_id)
        
#         if subcategory_id:
#             query = query.filter(Product.subcategory_id == subcategory_id)
        
#         if search:
#             search_term = f"%{search}%"
#             query = query.filter(
#                 Product.name.ilike(search_term) | 
#                 Product.description.ilike(search_term)
#             )
        
#         if min_price is not None:
#             min_price_cents = int(min_price * 100)
#             query = query.filter(Product.calculated_price >= min_price_cents)
        
#         if max_price is not None:
#             max_price_cents = int(max_price * 100)
#             query = query.filter(Product.calculated_price <= max_price_cents)
        
#         if is_active is not None:
#             query = query.filter(Product.is_active == is_active)
        
#         # Specification filtering using JSONB
#         if specifications:
#             try:
#                 spec_filters = json.loads(specifications)
#                 for key, value in spec_filters.items():
#                     query = query.filter(Product.specifications[key].astext == str(value))
#             except json.JSONDecodeError:
#                 raise HTTPException(status_code=400, detail="Invalid specifications JSON format")
        
#         # Get total count
#         total_count = query.count()
        
#         # Apply sorting
#         if sort_by == "calculated_price":
#             if sort_order == "desc":
#                 query = query.order_by(Product.calculated_price.desc())
#             else:
#                 query = query.order_by(Product.calculated_price.asc())
#         elif sort_by == "created_at":
#             if sort_order == "desc":
#                 query = query.order_by(Product.created_at.desc())
#             else:
#                 query = query.order_by(Product.created_at.asc())
#         elif sort_by == "stock_quantity":
#             if sort_order == "desc":
#                 query = query.order_by(Product.stock_quantity.desc())
#             else:
#                 query = query.order_by(Product.stock_quantity.asc())
#         else:  # Default to name
#             if sort_order == "desc":
#                 query = query.order_by(Product.name.desc())
#             else:
#                 query = query.order_by(Product.name.asc())
        
#         # Apply pagination
#         products = query.offset((page - 1) * per_page).limit(per_page).all()
        
#         # Calculate total pages
#         total_pages = (total_count + per_page - 1) // per_page
        
#         return ProductListResponse(
#             products=products,
#             total_count=total_count,
#             page=page,
#             per_page=per_page,
#             total_pages=total_pages
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to fetch products: {str(e)}")

# @router.get("/products/{product_id}", response_model=ProductResponse)
# async def get_product(product_id: int, db: Session = Depends(get_db)):
#     """Get a single product by ID"""
#     product = db.query(Product).options(
#         joinedload(Product.category),
#         joinedload(Product.subcategory)
#     ).filter(Product.product_id == product_id).first()
    
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     return product

# @router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
# async def create_product(
#     product_data: ProductCreate,
#     db: Session = Depends(get_db)
# ):
#     """Create a new product with dynamic specifications"""
#     try:
#         # Validate category and subcategory exist
#         category = db.query(Category).filter(Category.category_id == product_data.category_id).first()
#         if not category:
#             raise HTTPException(status_code=404, detail="Category not found")
        
#         subcategory = db.query(Subcategory).filter(
#             Subcategory.subcategory_id == product_data.subcategory_id,
#             Subcategory.category_id == product_data.category_id
#         ).first()
#         if not subcategory:
#             raise HTTPException(status_code=404, detail="Subcategory not found or doesn't belong to the specified category")
        
#         # Validate specifications against templates
#         pricing_service = PricingService(db)
#         validation = pricing_service.validate_specifications(
#             product_data.subcategory_id, 
#             product_data.specifications
#         )
        
#         if not validation["is_valid"]:
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Invalid specifications: {'; '.join(validation['errors'])}"
#             )
        
#         # Calculate final price
#         final_price, applied_rules, price_breakdown = pricing_service.calculate_price(
#             product_data.subcategory_id,
#             product_data.specifications,
#             product_data.base_price
#         )
        
#         # Create product
#         product = Product(
#             name=product_data.name,
#             description=product_data.description,
#             category_id=product_data.category_id,
#             subcategory_id=product_data.subcategory_id,
#             specifications=product_data.specifications,
#             base_price=product_data.base_price,
#             calculated_price=final_price,
#             stock_quantity=product_data.stock_quantity,
#             sku=product_data.sku,
#             created_by=product_data.created_by,
#             is_active=product_data.is_active
#         )
        
#         db.add(product)
#         db.commit()
#         db.refresh(product)
        
#         # Load relationships for response
#         product = db.query(Product).options(
#             joinedload(Product.category),
#             joinedload(Product.subcategory)
#         ).filter(Product.product_id == product.product_id).first()
        
#         return product
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

# @router.post("/products/with-images", status_code=status.HTTP_201_CREATED)
# async def create_product_with_images(
#     name: str = Form(...),
#     description: Optional[str] = Form(None),
#     category_id: int = Form(...),
#     subcategory_id: int = Form(...),
#     specifications: str = Form(..., description="JSON string of specifications"),
#     base_price: int = Form(..., description="Base price in cents"),
#     stock_quantity: int = Form(0),
#     sku: Optional[str] = Form(None),
#     created_by: str = Form(...),
#     images: List[UploadFile] = File(...),
#     db: Session = Depends(get_db)
# ):
#     """Create a product with images and dynamic specifications"""
#     try:
#         # Parse specifications JSON
#         try:
#             spec_dict = json.loads(specifications)
#         except json.JSONDecodeError:
#             raise HTTPException(status_code=400, detail="Invalid specifications JSON format")
        
#         # Validate category and subcategory
#         category = db.query(Category).filter(Category.category_id == category_id).first()
#         if not category:
#             raise HTTPException(status_code=404, detail="Category not found")
        
#         subcategory = db.query(Subcategory).filter(
#             Subcategory.subcategory_id == subcategory_id,
#             Subcategory.category_id == category_id
#         ).first()
#         if not subcategory:
#             raise HTTPException(status_code=404, detail="Subcategory not found")
        
#         # Validate specifications and calculate price
#         pricing_service = PricingService(db)
#         validation = pricing_service.validate_specifications(subcategory_id, spec_dict)
        
#         if not validation["is_valid"]:
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Invalid specifications: {'; '.join(validation['errors'])}"
#             )
        
#         final_price, applied_rules, price_breakdown = pricing_service.calculate_price(
#             subcategory_id, spec_dict, base_price
#         )
        
#         # Create product
#         product = Product(
#             name=name,
#             description=description,
#             category_id=category_id,
#             subcategory_id=subcategory_id,
#             specifications=spec_dict,
#             base_price=base_price,
#             calculated_price=final_price,
#             stock_quantity=stock_quantity,
#             sku=sku,
#             created_by=created_by
#         )
        
#         db.add(product)
#         db.commit()
#         db.refresh(product)
        
#         # Upload images (reuse existing image upload logic)
#         file_service = FileService()
#         upload_results = await file_service.save_multiple_product_images(
#             images, created_by, product.product_id
#         )
        
#         # Save image records (simplified version of existing logic)
#         from src.models.product_image import ProductImage
#         saved_images = []
        
#         for i, file_info in enumerate(upload_results["saved_files"]):
#             is_primary = (i == 0)
            
#             product_image = ProductImage(
#                 product_id=product.product_id,
#                 image_filename=file_info["filename"],
#                 image_path=file_info["file_path"],
#                 image_url=file_info["image_url"],
#                 alt_text=f"{product.name} - Image {i+1}",
#                 is_primary=is_primary,
#                 display_order=i + 1,
#                 uploaded_by=created_by,
#                 file_size=file_info["file_size"],
#                 mime_type=file_info["mime_type"]
#             )
#             db.add(product_image)
#             saved_images.append(product_image)
            
#             if is_primary:
#                 product.primary_image_url = file_info["image_url"]
#                 product.primary_image_filename = file_info["filename"]
        
#         db.commit()
        
#         return {
#             "message": "Product created successfully",
#             "product": {
#                 "product_id": product.product_id,
#                 "name": product.name,
#                 "specifications": product.specifications,
#                 "base_price": product.base_price,
#                 "calculated_price": product.calculated_price,
#                 "price_breakdown": price_breakdown,
#                 "applied_rules": applied_rules
#             },
#             "images": [{
#                 "image_id": img.image_id,
#                 "image_url": img.image_url,
#                 "is_primary": img.is_primary
#             } for img in saved_images],
#             "upload_summary": upload_results
#         }
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

# @router.put("/products/{product_id}", response_model=ProductResponse)
# async def update_product(
#     product_id: int,
#     product_data: ProductUpdate,
#     db: Session = Depends(get_db)
# ):
#     """Update a product"""
#     product = db.query(Product).filter(Product.product_id == product_id).first()
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     try:
#         # If specifications are being updated, validate and recalculate price
#         if product_data.specifications is not None:
#             pricing_service = PricingService(db)
#             validation = pricing_service.validate_specifications(
#                 product.subcategory_id, 
#                 product_data.specifications
#             )
            
#             if not validation["is_valid"]:
#                 raise HTTPException(
#                     status_code=400, 
#                     detail=f"Invalid specifications: {'; '.join(validation['errors'])}"
#                 )
            
#             # Recalculate price with new specifications
#             final_price, _, _ = pricing_service.calculate_price(
#                 product.subcategory_id,
#                 product_data.specifications,
#                 product_data.base_price or product.base_price
#             )
            
#             product.calculated_price = final_price
        
#         # Update other fields
#         for field, value in product_data.dict(exclude_unset=True).items():
#             if field != "specifications":  # Already handled above
#                 setattr(product, field, value)
        
#         # Update specifications separately to ensure JSON handling
#         if product_data.specifications is not None:
#             product.specifications = product_data.specifications
        
#         db.commit()
#         db.refresh(product)
        
#         # Load relationships for response
#         product = db.query(Product).options(
#             joinedload(Product.category),
#             joinedload(Product.subcategory)
#         ).filter(Product.product_id == product_id).first()
        
#         return product
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")

# @router.delete("/products/{product_id}")
# async def delete_product(product_id: int, db: Session = Depends(get_db)):
#     """Soft delete a product"""
#     product = db.query(Product).filter(Product.product_id == product_id).first()
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     try:
#         product.is_active = False
#         db.commit()
#         return {"message": "Product deleted successfully"}
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")

# @router.get("/products/by-specifications")
# async def get_products_by_specifications(
#     subcategory_id: int = Query(...),
#     specifications: str = Query(..., description="JSON string of required specifications"),
#     db: Session = Depends(get_db)
# ):
#     """Find products matching specific specifications"""
#     try:
#         spec_filters = json.loads(specifications)
        
#         query = db.query(Product).filter(
#             Product.subcategory_id == subcategory_id,
#             Product.is_active == True
#         )
        
#         # Filter by each specification
#         for key, value in spec_filters.items():
#             query = query.filter(Product.specifications[key].astext == str(value))
        
#         products = query.all()
        
#         return {
#             "subcategory_id": subcategory_id,
#             "specifications": spec_filters,
#             "products": [
#                 {
#                     "product_id": p.product_id,
#                     "name": p.name,
#                     "specifications": p.specifications,
#                     "calculated_price": p.calculated_price / 100,  # Convert to dollars
#                     "stock_quantity": p.stock_quantity,
#                     "primary_image_url": p.primary_image_url
#                 } for p in products
#             ],
#             "total_found": len(products)
#         }
        
#     except json.JSONDecodeError:
#         raise HTTPException(status_code=400, detail="Invalid specifications JSON format")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to search products: {str(e)}")



# # src/api/v1/products.py - Fixed version
# from fastapi import APIRouter, Depends, HTTPException, status, Query
# from sqlalchemy.orm import Session, joinedload
# from typing import List, Optional
# from config.database import get_db
# from src.models.category import  Category, Subcategory
# from src.models.product import Product
# from src.schemas.product import (
#     ProductResponse, 
#     ProductCreate, 
#     ProductUpdate,
#     ProductListResponse

# )
# from src.services.pricing_service import PricingService

# router = APIRouter()

# @router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
# async def create_product(
#     product_data: ProductCreate,
#     db: Session = Depends(get_db)
# ):
#     """Create a new product"""
#     try:
#         # Verify category exists
#         category = db.query(Category).filter(Category.category_id == product_data.category_id).first()
#         if not category:
#             raise HTTPException(status_code=404, detail="Category not found")
        
#         # Verify subcategory exists
#         subcategory = db.query(Subcategory).filter(Subcategory.subcategory_id == product_data.subcategory_id).first()
#         if not subcategory:
#             raise HTTPException(status_code=404, detail="Subcategory not found")
        
#         # Check if SKU already exists (if provided)
#         if product_data.sku:
#             existing_sku = db.query(Product).filter(Product.sku == product_data.sku).first()
#             if existing_sku:
#                 raise HTTPException(status_code=400, detail=f"SKU '{product_data.sku}' already exists")
        
#         # Create product
#         product_dict = product_data.model_dump()
#         product = Product(**product_dict)
        
#         # Calculate price using pricing service
#         if product_data.specifications:
#             pricing_service = PricingService(db)
#             calculated_price, _, _ = pricing_service.calculate_price(
#                 product_data.subcategory_id,
#                 product_data.specifications,
#                 product_data.base_price
#             )
#             product.calculated_price = calculated_price
#         else:
#             product.calculated_price = product_data.base_price
        
#         db.add(product)
#         db.commit()
#         db.refresh(product)
        
#         # Load related data for response
#         product_with_relations = db.query(Product)\
#             .options(joinedload(Product.category), joinedload(Product.subcategory))\
#             .filter(Product.product_id == product.product_id)\
#             .first()
        
#         # Convert to response format
#         response_data = {
#             **product_with_relations.__dict__,
#             "category": {
#                 "category_id": product_with_relations.category.category_id,
#                 "name": product_with_relations.category.name,
#                 "description": product_with_relations.category.description
#             } if product_with_relations.category else None,
#             "subcategory": {
#                 "subcategory_id": product_with_relations.subcategory.subcategory_id,
#                 "name": product_with_relations.subcategory.name,
#                 "description": product_with_relations.subcategory.description
#             } if product_with_relations.subcategory else None
#         }
        
#         return ProductResponse(**response_data)
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

# @router.get("/products", response_model=ProductListResponse)
# async def get_products(
#     page: int = Query(1, ge=1),
#     per_page: int = Query(10, ge=1, le=100),
#     category_id: Optional[int] = Query(None),
#     subcategory_id: Optional[int] = Query(None),
#     is_active: Optional[bool] = Query(None),
#     search: Optional[str] = Query(None),
#     db: Session = Depends(get_db)
# ):
#     """Get products with pagination and filters"""
#     query = db.query(Product).options(
#         joinedload(Product.category),
#         joinedload(Product.subcategory)
#     )
    
#     # Apply filters
#     if category_id:
#         query = query.filter(Product.category_id == category_id)
#     if subcategory_id:
#         query = query.filter(Product.subcategory_id == subcategory_id)
#     if is_active is not None:
#         query = query.filter(Product.is_active == is_active)
#     if search:
#         query = query.filter(Product.name.ilike(f"%{search}%"))
    
#     # Get total count
#     total_count = query.count()
    
#     # Apply pagination
#     offset = (page - 1) * per_page
#     products = query.offset(offset).limit(per_page).all()
    
#     # Convert products to response format
#     product_responses = []
#     for product in products:
#         response_data = {
#             **product.__dict__,
#             "category": {
#                 "category_id": product.category.category_id,
#                 "name": product.category.name,
#                 "description": product.category.description
#             } if product.category else None,
#             "subcategory": {
#                 "subcategory_id": product.subcategory.subcategory_id,
#                 "name": product.subcategory.name,
#                 "description": product.subcategory.description
#             } if product.subcategory else None
#         }
#         product_responses.append(ProductResponse(**response_data))
    
#     total_pages = (total_count + per_page - 1) // per_page
    
#     return ProductListResponse(
#         products=product_responses,
#         total_count=total_count,
#         page=page,
#         per_page=per_page,
#         total_pages=total_pages
#     )

# @router.get("/products/{product_id}", response_model=ProductResponse)
# async def get_product(product_id: int, db: Session = Depends(get_db)):
#     """Get product by ID"""
#     product = db.query(Product)\
#         .options(joinedload(Product.category), joinedload(Product.subcategory))\
#         .filter(Product.product_id == product_id)\
#         .first()
    
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     # Convert to response format
#     response_data = {
#         **product.__dict__,
#         "category": {
#             "category_id": product.category.category_id,
#             "name": product.category.name,
#             "description": product.category.description
#         } if product.category else None,
#         "subcategory": {
#             "subcategory_id": product.subcategory.subcategory_id,
#             "name": product.subcategory.name,
#             "description": product.subcategory.description
#         } if product.subcategory else None
#     }
    
#     return ProductResponse(**response_data)

# @router.put("/products/{product_id}", response_model=ProductResponse)
# async def update_product(
#     product_id: int,
#     product_data: ProductUpdate,
#     db: Session = Depends(get_db)
# ):
#     """Update a product"""
#     product = db.query(Product).filter(Product.product_id == product_id).first()
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     try:
#         # Check SKU uniqueness if updating SKU
#         update_dict = product_data.model_dump(exclude_unset=True)
#         if 'sku' in update_dict and update_dict['sku']:
#             existing_sku = db.query(Product).filter(
#                 Product.sku == update_dict['sku'],
#                 Product.product_id != product_id
#             ).first()
#             if existing_sku:
#                 raise HTTPException(status_code=400, detail=f"SKU '{update_dict['sku']}' already exists")
        
#         # Update fields
#         for field, value in update_dict.items():
#             setattr(product, field, value)
        
#         # Recalculate price if specifications or base_price changed
#         if 'specifications' in update_dict or 'base_price' in update_dict:
#             pricing_service = PricingService(db)
#             calculated_price, _, _ = pricing_service.calculate_price(
#                 product.subcategory_id,
#                 product.specifications,
#                 product.base_price
#             )
#             product.calculated_price = calculated_price
        
#         db.commit()
#         db.refresh(product)
        
#         # Load with relations and return
#         product_with_relations = db.query(Product)\
#             .options(joinedload(Product.category), joinedload(Product.subcategory))\
#             .filter(Product.product_id == product_id)\
#             .first()
        
#         response_data = {
#             **product_with_relations.__dict__,
#             "category": {
#                 "category_id": product_with_relations.category.category_id,
#                 "name": product_with_relations.category.name,
#                 "description": product_with_relations.category.description
#             } if product_with_relations.category else None,
#             "subcategory": {
#                 "subcategory_id": product_with_relations.subcategory.subcategory_id,
#                 "name": product_with_relations.subcategory.name,
#                 "description": product_with_relations.subcategory.description
#             } if product_with_relations.subcategory else None
#         }
        
#         return ProductResponse(**response_data)
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")

# @router.delete("/products/{product_id}")
# async def delete_product(product_id: int, db: Session = Depends(get_db)):
#     """Delete a product"""
#     product = db.query(Product).filter(Product.product_id == product_id).first()
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     try:
#         db.delete(product)
#         db.commit()
#         return {"message": "Product deleted successfully"}
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")









# # src/api/v1/products.py - Updated to work with your existing FileService
# from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
# from sqlalchemy.orm import Session, joinedload
# from typing import List, Optional
# from config.database import get_db
# from src.models.category import Category, Subcategory
# from src.models.product import Product
# from src.models.product_image import ProductImage
# from src.schemas.product import ProductResponse, ProductListResponse
# from src.services.pricing_service import PricingService
# from src.services.file_service import FileService
# import json

# router = APIRouter()

# @router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
# async def create_product(
#     # Form data
#     name: str = Form(...),
#     description: Optional[str] = Form(None),
#     category_id: int = Form(...),
#     subcategory_id: int = Form(...),
#     specifications: str = Form("{}"),  # JSON string
#     base_price: int = Form(...),
#     stock_quantity: int = Form(0),
#     sku: Optional[str] = Form(None),
#     created_by: str = Form("admin"),
#     is_active: bool = Form(True),
    
#     # File uploads
#     images: List[UploadFile] = File([]),
    
#     # Dependencies
#     db: Session = Depends(get_db)
# ):
#     """Create a new product with images"""
#     try:
#         # Parse specifications JSON
#         try:
#             specs_dict = json.loads(specifications) if specifications else {}
#         except json.JSONDecodeError:
#             raise HTTPException(status_code=400, detail="Invalid specifications JSON")
        
#         # Verify category exists
#         category = db.query(Category).filter(Category.category_id == category_id).first()
#         if not category:
#             raise HTTPException(status_code=404, detail="Category not found")
        
#         # Verify subcategory exists
#         subcategory = db.query(Subcategory).filter(Subcategory.subcategory_id == subcategory_id).first()
#         if not subcategory:
#             raise HTTPException(status_code=404, detail="Subcategory not found")
        
#         # Check if SKU already exists (if provided)
#         if sku:
#             existing_sku = db.query(Product).filter(Product.sku == sku).first()
#             if existing_sku:
#                 raise HTTPException(status_code=400, detail=f"SKU '{sku}' already exists")
        
#         # Create product
#         product = Product(
#             name=name,
#             description=description,
#             category_id=category_id,
#             subcategory_id=subcategory_id,
#             specifications=specs_dict,
#             base_price=base_price,
#             stock_quantity=stock_quantity,
#             sku=sku,
#             created_by=created_by,
#             is_active=is_active
#         )
        
#         # Calculate price using pricing service
#         if specs_dict:
#             pricing_service = PricingService(db)
#             calculated_price, _, _ = pricing_service.calculate_price(
#                 subcategory_id,
#                 specs_dict,
#                 base_price
#             )
#             product.calculated_price = calculated_price
#         else:
#             product.calculated_price = base_price
        
#         # Save product first to get product_id
#         db.add(product)
#         db.flush()  # This assigns the product_id without committing
        
#         # Handle image uploads using your existing FileService
#         if images and any(img.filename for img in images if img.filename):
#             file_service = FileService()
            
#             # Filter out empty files
#             valid_images = [img for img in images if img.filename and img.filename.strip()]
            
#             if valid_images:
#                 # Use your existing file service method
#                 upload_result = await file_service.save_multiple_product_images(
#                     images=valid_images,
#                     sales_user=created_by,
#                     product_id=product.product_id
#                 )
                
#                 # Create ProductImage records for successfully uploaded files
#                 for i, file_info in enumerate(upload_result['saved_files']):
#                     # First image is primary by default
#                     is_primary = (i == 0)
                    
#                     product_image = ProductImage(
#                         product_id=product.product_id,
#                         image_filename=file_info['filename'],
#                         image_path=file_info['file_path'],
#                         image_url=file_info['image_url'],
#                         alt_text=f"{product.name} - Image {i+1}",
#                         is_primary=is_primary,
#                         display_order=i,
#                         file_size=file_info['file_size'],
#                         mime_type=file_info['mime_type'],
#                         uploaded_by=created_by
#                     )
#                     db.add(product_image)
                
#                 # Log any failed uploads
#                 if upload_result['failed_files']:
#                     print(f"Failed to upload {len(upload_result['failed_files'])} files:")
#                     for failed in upload_result['failed_files']:
#                         print(f"  - {failed['filename']}: {failed['error']}")
        
#         # Commit all changes
#         db.commit()
#         db.refresh(product)
        
#         # Load product with all relationships
#         product_with_relations = db.query(Product)\
#             .options(
#                 joinedload(Product.category),
#                 joinedload(Product.subcategory),
#                 joinedload(Product.images)
#             )\
#             .filter(Product.product_id == product.product_id)\
#             .first()
        
#         # Convert to response format
#         response_data = {
#             **product_with_relations.__dict__,
#             "category": {
#                 "category_id": product_with_relations.category.category_id,
#                 "name": product_with_relations.category.name,
#                 "description": product_with_relations.category.description
#             } if product_with_relations.category else None,
#             "subcategory": {
#                 "subcategory_id": product_with_relations.subcategory.subcategory_id,
#                 "name": product_with_relations.subcategory.name,
#                 "description": product_with_relations.subcategory.description
#             } if product_with_relations.subcategory else None,
#             "primary_image_url": product_with_relations.primary_image_url,
#             "primary_image_filename": product_with_relations.primary_image_filename
#         }
        
#         return ProductResponse(**response_data)
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

# @router.get("/products", response_model=ProductListResponse)
# async def get_products(
#     page: int = Query(1, ge=1),
#     per_page: int = Query(10, ge=1, le=100),
#     category_id: Optional[int] = Query(None),
#     subcategory_id: Optional[int] = Query(None),
#     is_active: Optional[bool] = Query(None),
#     search: Optional[str] = Query(None),
#     db: Session = Depends(get_db)
# ):
#     """Get products with pagination and filters"""
#     query = db.query(Product).options(
#         joinedload(Product.category),
#         joinedload(Product.subcategory),
#         joinedload(Product.images)
#     )
    
#     # Apply filters
#     if category_id:
#         query = query.filter(Product.category_id == category_id)
#     if subcategory_id:
#         query = query.filter(Product.subcategory_id == subcategory_id)
#     if is_active is not None:
#         query = query.filter(Product.is_active == is_active)
#     if search:
#         query = query.filter(Product.name.ilike(f"%{search}%"))
    
#     # Get total count
#     total_count = query.count()
    
#     # Apply pagination
#     offset = (page - 1) * per_page
#     products = query.offset(offset).limit(per_page).all()
    
#     # Convert products to response format
#     product_responses = []
#     for product in products:
#         response_data = {
#             **product.__dict__,
#             "category": {
#                 "category_id": product.category.category_id,
#                 "name": product.category.name,
#                 "description": product.category.description
#             } if product.category else None,
#             "subcategory": {
#                 "subcategory_id": product.subcategory.subcategory_id,
#                 "name": product.subcategory.name,
#                 "description": product.subcategory.description
#             } if product.subcategory else None,
#             "primary_image_url": product.primary_image_url,
#             "primary_image_filename": product.primary_image_filename
#         }
#         product_responses.append(ProductResponse(**response_data))
    
#     total_pages = (total_count + per_page - 1) // per_page
    
#     return ProductListResponse(
#         products=product_responses,
#         total_count=total_count,
#         page=page,
#         per_page=per_page,
#         total_pages=total_pages
#     )

# @router.get("/products/{product_id}", response_model=ProductResponse)
# async def get_product(product_id: int, db: Session = Depends(get_db)):
#     """Get product by ID with images"""
#     product = db.query(Product)\
#         .options(
#             joinedload(Product.category), 
#             joinedload(Product.subcategory),
#             joinedload(Product.images)
#         )\
#         .filter(Product.product_id == product_id)\
#         .first()
    
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     # Convert to response format
#     response_data = {
#         **product.__dict__,
#         "category": {
#             "category_id": product.category.category_id,
#             "name": product.category.name,
#             "description": product.category.description
#         } if product.category else None,
#         "subcategory": {
#             "subcategory_id": product.subcategory.subcategory_id,
#             "name": product.subcategory.name,
#             "description": product.subcategory.description
#         } if product.subcategory else None,
#         "primary_image_url": product.primary_image_url,
#         "primary_image_filename": product.primary_image_filename
#     }
    
#     return ProductResponse(**response_data)

# @router.get("/products/{product_id}/images")
# async def get_product_images(product_id: int, db: Session = Depends(get_db)):
#     """Get all images for a product"""
#     product = db.query(Product).filter(Product.product_id == product_id).first()
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     images = db.query(ProductImage)\
#         .filter(ProductImage.product_id == product_id)\
#         .order_by(ProductImage.display_order, ProductImage.created_at)\
#         .all()
    
#     return {
#         "product_id": product_id,
#         "product_name": product.name,
#         "total_images": len(images),
#         "images": images
#     }

# @router.delete("/products/{product_id}/images/{image_id}")
# async def delete_product_image(
#     product_id: int, 
#     image_id: int, 
#     db: Session = Depends(get_db)
# ):
#     """Delete a specific product image"""
#     # Find the image
#     image = db.query(ProductImage).filter(
#         ProductImage.image_id == image_id,
#         ProductImage.product_id == product_id
#     ).first()
    
#     if not image:
#         raise HTTPException(status_code=404, detail="Image not found")
    
#     try:
#         # Delete file from filesystem using your FileService
#         file_service = FileService()
#         file_deleted = file_service.delete_file(image.image_path)
        
#         # Delete from database
#         db.delete(image)
        
#         # If this was the primary image, make another image primary
#         if image.is_primary:
#             next_primary = db.query(ProductImage).filter(
#                 ProductImage.product_id == product_id,
#                 ProductImage.image_id != image_id
#             ).first()
            
#             if next_primary:
#                 next_primary.is_primary = True
        
#         db.commit()
        
#         return {
#             "message": "Image deleted successfully",
#             "file_deleted": file_deleted
#         }
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

# @router.put("/products/{product_id}/images/{image_id}/primary")
# async def set_primary_image(
#     product_id: int, 
#     image_id: int, 
#     db: Session = Depends(get_db)
# ):
#     """Set an image as the primary image for a product"""
#     # Verify the image exists and belongs to the product
#     image = db.query(ProductImage).filter(
#         ProductImage.image_id == image_id,
#         ProductImage.product_id == product_id
#     ).first()
    
#     if not image:
#         raise HTTPException(status_code=404, detail="Image not found")
    
#     try:
#         # Remove primary flag from all images of this product
#         db.query(ProductImage).filter(
#             ProductImage.product_id == product_id
#         ).update({"is_primary": False})
        
#         # Set this image as primary
#         image.is_primary = True
        
#         db.commit()
        
#         return {"message": "Primary image updated successfully"}
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to update primary image: {str(e)}")



# src/api/v1/products.py - Debug version with better error handling
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from sqlalchemy.orm import Session, joinedload
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
    """Create a new product with images - debug version"""
    try:
        # Log incoming data for debugging
        logger.info(f"Creating product: {name}")
        logger.info(f"Category ID: {category_id}, Subcategory ID: {subcategory_id}")
        logger.info(f"Base price: {base_price}, Stock: {stock_quantity}")
        logger.info(f"Images count: {len(images) if images else 0}")
        
        # Convert and validate data types
        try:
            base_price_int = int(float(base_price))  # Convert to int (assuming it's in cents from frontend)
            stock_quantity_int = int(stock_quantity) if stock_quantity else 0
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
        except (ValueError, TypeError) as e:
            logger.error(f"Data conversion error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid data format: {str(e)}")
        
        # Parse specifications JSON
        try:
            specs_dict = json.loads(specifications) if specifications and specifications != '{}' else {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid specifications JSON: {str(e)}")
        
        # Verify category exists
        category = db.query(Category).filter(Category.category_id == category_id).first()
        if not category:
            logger.error(f"Category {category_id} not found")
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Verify subcategory exists
        subcategory = db.query(Subcategory).filter(Subcategory.subcategory_id == subcategory_id).first()
        if not subcategory:
            logger.error(f"Subcategory {subcategory_id} not found")
            raise HTTPException(status_code=404, detail="Subcategory not found")
        
        # Check if SKU already exists (if provided)
        if sku and sku.strip():
            existing_sku = db.query(Product).filter(Product.sku == sku).first()
            if existing_sku:
                raise HTTPException(status_code=400, detail=f"SKU '{sku}' already exists")
        
        # Create product with validated data
        product = Product(
            name=name,
            description=description if description else None,
            category_id=category_id,
            subcategory_id=subcategory_id,
            specifications=specs_dict,
            base_price=base_price_int,
            stock_quantity=stock_quantity_int,
            sku=sku if sku.strip() else None,
            created_by=created_by,
            is_active=is_active_bool
        )
        
        # Calculate price using pricing service if available
        try:
            if specs_dict and hasattr(PricingService, '__init__'):
                pricing_service = PricingService(db)
                calculated_price, _, _ = pricing_service.calculate_price(
                    subcategory_id,
                    specs_dict,
                    base_price_int
                )
                product.calculated_price = calculated_price
            else:
                product.calculated_price = base_price_int
        except Exception as e:
            logger.warning(f"Price calculation failed: {e}")
            product.calculated_price = base_price_int
        
        # Save product first to get product_id
        db.add(product)
        db.flush()  # This assigns the product_id without committing
        logger.info(f"Product created with ID: {product.product_id}")
        
        # Handle image uploads using your existing FileService
        if images and len(images) > 0:
            # Filter out empty files
            valid_images = [img for img in images if img.filename and img.filename.strip()]
            logger.info(f"Valid images to upload: {len(valid_images)}")
            
            if valid_images:
                try:
                    file_service = FileService()
                    
                    # Use your existing file service method
                    upload_result = await file_service.save_multiple_product_images(
                        images=valid_images,
                        sales_user=created_by,
                        product_id=product.product_id
                    )
                    
                    logger.info(f"Upload result: {upload_result['total_uploaded']} uploaded, {upload_result['total_failed']} failed")
                    
                    # Create ProductImage records for successfully uploaded files
                    for i, file_info in enumerate(upload_result['saved_files']):
                        # First image is primary by default
                        is_primary = (i == 0)
                        
                        product_image = ProductImage(
                            product_id=product.product_id,
                            image_filename=file_info['filename'],
                            image_path=file_info['file_path'],
                            image_url=file_info['image_url'],
                            alt_text=f"{product.name} - Image {i+1}",
                            is_primary=is_primary,
                            display_order=i,
                            file_size=file_info['file_size'],
                            mime_type=file_info['mime_type'],
                            uploaded_by=created_by
                        )
                        db.add(product_image)
                    
                    # Log any failed uploads
                    if upload_result['failed_files']:
                        logger.warning(f"Failed to upload {len(upload_result['failed_files'])} files:")
                        for failed in upload_result['failed_files']:
                            logger.warning(f"  - {failed['filename']}: {failed['error']}")
                      # ✅ Set primary image URL and filename on the product
                    primary_image = next((img for i, img in enumerate(upload_result['saved_files']) if i == 0), None)
                    if primary_image:
                        product.primary_image_url = primary_image.get("image_url")
                        product.primary_image_filename = primary_image.get("filename")

                    if upload_result['failed_files']:
                        logger.warning(f"Failed to upload {len(upload_result['failed_files'])} files:")
                        for failed in upload_result['failed_files']:
                            logger.warning(f"  - {failed['filename']}: {failed['error']}")      
                except Exception as e:
                    logger.error(f"Image upload failed: {e}")
                    # Don't fail the entire product creation if images fail
                    # Just log the error and continue
        
        # Commit all changes
        db.commit()
        db.refresh(product)
        logger.info(f"Product {product.product_id} successfully created")
        
        # Load product with all relationships
        product_with_relations = db.query(Product)\
            .options(
                joinedload(Product.category),
                joinedload(Product.subcategory),
                joinedload(Product.images)
            )\
            .filter(Product.product_id == product.product_id)\
            .first()
        
        # Convert to response format
        response_data = {
            "product_id": product_with_relations.product_id,
            "name": product_with_relations.name,
            "description": product_with_relations.description,
            "category_id": product_with_relations.category_id,
            "subcategory_id": product_with_relations.subcategory_id,
            "specifications": product_with_relations.specifications,
            "base_price": product_with_relations.base_price,
            "calculated_price": product_with_relations.calculated_price,
            "stock_quantity": product_with_relations.stock_quantity,
            "sku": product_with_relations.sku,
            "is_active": product_with_relations.is_active,
            "created_by": product_with_relations.created_by,
            "created_at": product_with_relations.created_at,
            "updated_at": product_with_relations.updated_at,
            "category": {
                "category_id": product_with_relations.category.category_id,
                "name": product_with_relations.category.name,
                "description": product_with_relations.category.description
            } if product_with_relations.category else None,
            "subcategory": {
                "subcategory_id": product_with_relations.subcategory.subcategory_id,
                "name": product_with_relations.subcategory.name,
                "description": product_with_relations.subcategory.description
            } if product_with_relations.subcategory else None,
            "primary_image_url": product_with_relations.primary_image_url,
            "primary_image_filename": product_with_relations.primary_image_filename
        }
        
        return ProductResponse(**response_data)
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating product: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

# Add a simple test endpoint to debug form data
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

# Your existing GET endpoints (unchanged)
@router.get("/products", response_model=ProductListResponse)
async def get_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    subcategory_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get products with pagination and filters"""
    query = db.query(Product).options(
        joinedload(Product.category),
        joinedload(Product.subcategory),
        joinedload(Product.images)
    )
    
    # Apply filters
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if subcategory_id:
        query = query.filter(Product.subcategory_id == subcategory_id)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    products = query.offset(offset).limit(per_page).all()
    
    # Convert products to response format
    product_responses = []
    for product in products:
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
    
    return ProductListResponse(
        products=product_responses,
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
