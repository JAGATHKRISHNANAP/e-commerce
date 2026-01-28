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


@router.get("/products/filters")
async def get_product_filters(
    category_id: Optional[int] = Query(None),
    subcategory_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get dynamic filters based on available product specifications.
    Returns a dictionary like: {"Color": ["Red", "Blue"], "Size": ["S", "M"]}
    """
    query = db.query(Product.specifications).filter(Product.is_active == True)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if subcategory_id:
        query = query.filter(Product.subcategory_id == subcategory_id)
        
    products_specs = query.all()
    
    # Aggregate filters
    filters = {}
    for (specs,) in products_specs:
        if specs and isinstance(specs, dict):
            for key, value in specs.items():
                if key not in filters:
                    filters[key] = set()
                filters[key].add(str(value))
                
    # Convert sets to sorted lists
    return {k: sorted(list(v)) for k, v in filters.items()}

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
    group_by_variants: bool = Query(True, description="Group variants into a single product card"),
    db: Session = Depends(get_db)
):
    """
    Get list of products with pagination, filtering, sorting, and search.
    Groups variants (returns only one representative per group) unless group_by_variants=False.
    """
    try:
        from sqlalchemy import or_, func, and_
        
        logger.info(f"Product search - Category: {category_id}, Subcategory: {subcategory_id}")
        logger.info(f"Price range: {min_price} - {max_price}")
        logger.info(f"Sort: {sort_by} {sort_order}")
        
        # Base query
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
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.sku.ilike(search_term)
                )
            )
            
        # Price range filter
        if min_price is not None:
             min_cents = int(min_price * 100)
             query = query.filter(func.coalesce(Product.calculated_price, Product.base_price) >= min_cents)
             
        if max_price is not None:
             max_cents = int(max_price * 100)
             query = query.filter(func.coalesce(Product.calculated_price, Product.base_price) <= max_cents)

        # GROUPING LOGIC: Deduplicate variants (only if requested)
        if group_by_variants:
            # Subquery to find the 'representative' product_id for each group
            # We need to respect is_active in the subquery if applied above
            subq_filter = Product.group_id.isnot(None)
            if is_active is not None:
                 subq_filter = and_(Product.group_id.isnot(None), Product.is_active == is_active)
                
            representative_subquery = db.query(func.min(Product.product_id))\
                .filter(subq_filter)\
                .group_by(Product.group_id)
                
            query = query.filter(
                or_(
                    Product.group_id.is_(None),
                    Product.product_id.in_(representative_subquery)
                )
            )
        else:
            logger.info("Variant grouping disabled - showing all products")


# ... rest of pagination/sorting logic is preserved in file content below this block? 
# NO, I need to include the rest of the function because I'm replacing the top half and might break it.
# Let's include the whole function to be safe.

        # Count total before pagination
        total_count = query.count()
        
        # Sorting
        if sort_by == 'price':
            sort_attr = Product.base_price
        elif sort_by == 'created_at':
            sort_attr = Product.created_at
        else: # default to name
            sort_attr = Product.name
            
        if sort_order == 'desc':
            query = query.order_by(sort_attr.desc())
        else:
            query = query.order_by(sort_attr.asc())
            
        # Pagination
        offset = (page - 1) * per_page
        products = query.offset(offset).limit(per_page).all()
        
        # Convert to dictionary list to avoid SQLAlchemy/Pydantic conflicts
        results = []
        for p in products:
            # Handle calculated_price safety
            calc_price = p.calculated_price if p.calculated_price is not None else p.base_price
            
            item = {
                "product_id": p.product_id,
                "name": p.name,
                "description": p.description,
                "base_price": p.base_price,
                "calculated_price": calc_price,
                "stock_quantity": p.stock_quantity,
                "category_id": p.category_id,
                "subcategory_id": p.subcategory_id,
                "created_by": p.created_by,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "is_active": p.is_active,
                "sku": p.sku,
                "specifications": p.specifications or {},
                "primary_image_url": p.primary_image_url,
                "primary_image_filename": p.primary_image_filename,
                "group_id": p.group_id,
                "variants": [],
                "images": p.images # ORM list, Pydantic should handle this conversion
            }
            
            # Handle dictionary fields
            if p.category:
                item["category"] = {
                    "category_id": p.category.category_id,
                    "name": p.category.name
                }
            else:
                item["category"] = None
                
            if p.subcategory:
                item["subcategory"] = {
                    "subcategory_id": p.subcategory.subcategory_id,
                    "name": p.subcategory.name
                }
            else:
                item["subcategory"] = None
                
            results.append(item)
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return ProductListResponse(
            products=results,
            total_count=total_count,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
            
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


# NEW: Auto-group products
@router.post("/products/auto-group")
async def auto_group_products(db: Session = Depends(get_db)):
    """Automatically group products with similar names (ignoring case and whitespace)"""
    try:
        products = db.query(Product).filter(Product.is_active == True).all()
        grouped_count = 0
        
        # Simple grouping logic: normalize name (lowercase, strip) -> list of products
        name_map = {}
        for p in products:
            normalized_name = p.name.lower().strip()
            # Remove variant keywords for grouping if needed, but strict name match is safer for now
            # "Kurthi" vs "Kurthi Red" - we probably want to group by base Name "Kurthi"
            # For this iteration, let's assume products have SAME NAME but different specs
            # If names differ ("Red Kurthi" vs "Blue Kurthi"), this won't group them yet.
            # User said "product is kurthi with different color", implying name is "Kurthi".
            
            if normalized_name not in name_map:
                name_map[normalized_name] = []
            name_map[normalized_name].append(p)
            
        for name, group in name_map.items():
            if len(group) > 1:
                # Generate a group ID for this batch
                import uuid
                new_group_id = str(uuid.uuid4())
                
                for p in group:
                    if not p.group_id: # Only assign if not already grouped? Or overwrite? Overwrite for now.
                        p.group_id = new_group_id
                        grouped_count += 1
        
        db.commit()
        return {"message": f"Grouped {grouped_count} products into {len([g for g in name_map.values() if len(g)>1])} groups"}
        
    except Exception as e:
        logger.error(f"Auto-grouping failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID with variants"""
    # Fetch main product
    product = db.query(Product)\
        .options(
            joinedload(Product.category),
            joinedload(Product.subcategory),
            joinedload(Product.images)
        )\
        .filter(Product.product_id == product_id)\
        .first()
        
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # Prepare response object manually to avoid SQLAlchemy/Pydantic conflicts
    # Check for variants (siblings with same group_id)
    variants_list = []
    if product.group_id:
        siblings = db.query(Product.product_id, Product.specifications)\
            .filter(Product.group_id == product.group_id)\
            .filter(Product.product_id != product_id)\
            .all()
            
        for sib_id, sib_specs in siblings:
            variants_list.append({
                "product_id": sib_id,
                "specifications": sib_specs or {}
            })
            
    # Calculate display price
    calc_price = product.calculated_price if product.calculated_price is not None else product.base_price

    response_data = {
        "product_id": product.product_id,
        "name": product.name,
        "description": product.description,
        "base_price": product.base_price,
        "calculated_price": calc_price,
        "stock_quantity": product.stock_quantity,
        "category_id": product.category_id,
        "subcategory_id": product.subcategory_id,
        "created_by": product.created_by,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "is_active": product.is_active,
        "sku": product.sku,
        "specifications": product.specifications or {},
        "primary_image_url": product.primary_image_url,
        "primary_image_filename": product.primary_image_filename,
        "group_id": product.group_id,
        "variants": variants_list,
        "images": product.images, # Pydantic handles ORM list conversion nicely usually
        "category": {
            "category_id": product.category.category_id,
            "name": product.category.name,
            "description": product.category.description
        } if product.category else None,
        "subcategory": {
            "subcategory_id": product.subcategory.subcategory_id,
            "name": product.subcategory.name,
            "description": product.subcategory.description
        } if product.subcategory else None
    }
    
    return ProductResponse(**response_data)

# Your existing test endpoint remains unchanged
@router.post("/products/test")
async def test_form_data(
    name: str = Form(...),
# ... rest of file (update_product, delete_image) ...
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
# NEW: Get all images for a specific product
@router.get("/products/{product_id}/images")
async def get_product_images(product_id: int, db: Session = Depends(get_db)):
    """Get all images for a product"""
    try:
        # Check if product exists
        product = db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        # Get images
        images = db.query(ProductImage).filter(ProductImage.product_id == product_id).order_by(ProductImage.display_order).all()
        
        return {
            "product_id": product_id,
            "images": [
                {
                    "image_id": img.image_id,
                    "image_url": img.image_url,
                    "filename": img.image_filename,
                    "is_primary": img.is_primary,
                    "display_order": img.display_order
                } for img in images
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product images: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
# NEW: Update product
@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    # Form data - all optional
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    subcategory_id: Optional[int] = Form(None),
    specifications: Optional[str] = Form(None),  # JSON string
    base_price: Optional[str] = Form(None),
    stock_quantity: Optional[str] = Form(None),
    sku: Optional[str] = Form(None),
    is_active: Optional[str] = Form(None),
    
    # File uploads - optional
    images: List[UploadFile] = File(default=[]),
    
    # Dependencies
    db: Session = Depends(get_db)
):
    """Update an existing product"""
    try:
        # Get existing product
        product = db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        logger.info(f"Updating product {product_id}")
        
        # Update fields if provided
        if name is not None:
            product.name = name
            
        if description is not None:
            product.description = description
            
        if category_id is not None:
            # Verify category exists
            category = db.query(Category).filter(Category.category_id == category_id).first()
            if not category:
                raise HTTPException(status_code=404, detail=f"Category {category_id} not found")
            product.category_id = category_id
            
        if subcategory_id is not None:
            # Verify subcategory exists
            subcategory = db.query(Subcategory).filter(Subcategory.subcategory_id == subcategory_id).first()
            if not subcategory:
                raise HTTPException(status_code=404, detail=f"Subcategory {subcategory_id} not found")
            product.subcategory_id = subcategory_id
            
        if sku is not None:
            # Check for uniqueness if SKU changed
            if sku != product.sku:
                 existing_sku = db.query(Product).filter(Product.sku == sku).first()
                 if existing_sku:
                     raise HTTPException(status_code=400, detail=f"SKU '{sku}' already exists")
            product.sku = sku

        if is_active is not None:
             product.is_active = is_active.lower() in ('true', '1', 'yes')

        if base_price is not None:
            try:
                base_price_int = int(float(base_price))
                product.base_price = base_price_int
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Invalid base_price format")

        if stock_quantity is not None:
            try:
                product.stock_quantity = int(stock_quantity)
            except (ValueError, TypeError):
                 raise HTTPException(status_code=400, detail="Invalid stock_quantity format")
                 
        if specifications is not None:
            try:
                specs_dict = json.loads(specifications) if specifications and specifications != '{}' else {}
                product.specifications = specs_dict
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid specifications JSON")

        # Recalculate price if necessary
        # Simplified: just update calculated_price unless we want to run full pricing rules again
        # For now, let's re-run basic calculation if base_price changed
        # ideally we should use the service
        try:
             # Use the service if we have it/can import it, or just basic assignment
             if hasattr(PricingService, '__init__'):
                 pricing_service = PricingService(db)
                 calculated_price, _, _ = pricing_service.calculate_price(
                     product.subcategory_id,
                     product.specifications or {},
                     product.base_price
                 )
                 product.calculated_price = calculated_price
             else:
                 product.calculated_price = product.base_price
        except Exception as e:
            logger.warning(f"Price recalc failed: {e}")
            product.calculated_price = product.base_price

        # Handle new images
        if images and len(images) > 0:
            valid_images = [img for img in images if img.filename and img.filename.strip()]
            if valid_images:
                try:
                    file_service = FileService()
                    upload_result = await file_service.save_multiple_product_images(
                        images=valid_images,
                        sales_user=product.created_by, # Keep original creator or use current user? Using original for path consistency
                        product_id=product.product_id
                    )
                    
                    # Get max display order
                    max_order = db.query(func.max(ProductImage.display_order)).filter(ProductImage.product_id == product_id).scalar() or 0
                    
                    for i, file_info in enumerate(upload_result['saved_files']):
                        product_image = ProductImage(
                            product_id=product.product_id,
                            image_filename=file_info['filename'],
                            image_path=file_info['file_path'],
                            image_url=file_info['image_url'],
                            alt_text=f"{product.name} - Image",
                            is_primary=False, # New images not primary by default
                            display_order=max_order + i + 1,
                            file_size=file_info['file_size'],
                            mime_type=file_info['mime_type'],
                            uploaded_by=product.created_by
                        )
                        db.add(product_image)
                        
                    # Update primary image if none exists
                    if not product.primary_image_url and upload_result['saved_files']:
                         first_img = upload_result['saved_files'][0]
                         product.primary_image_url = first_img['image_url']
                         product.primary_image_filename = first_img['filename']
                         
                except Exception as e:
                    logger.error(f"Image upload failed during update: {e}")

        db.commit()
        db.refresh(product)
        
        # Reload with relations
        product_with_relations = db.query(Product)\
            .options(
                joinedload(Product.category),
                joinedload(Product.subcategory),
                joinedload(Product.images)
            )\
            .filter(Product.product_id == product.product_id)\
            .first()

        # Construct response (same logic as create/get)
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
        logger.error(f"Unexpected error updating product: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")

# NEW: Delete product image
@router.delete("/products/{product_id}/images/{image_id}")
async def delete_product_image(product_id: int, image_id: int, db: Session = Depends(get_db)):
    """Delete a product image"""
    try:
        image = db.query(ProductImage).filter(
            ProductImage.image_id == image_id,
            ProductImage.product_id == product_id
        ).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
            
        # Optional: Delete file from disk (FileService)
        # For now, just delete DB record to act fast
        
        db.delete(image)
        
        # If primary, pick a new one
        if image.is_primary:
            new_primary = db.query(ProductImage).filter(
                ProductImage.product_id == product_id,
                ProductImage.image_id != image_id
            ).first()
            
            product = db.query(Product).filter(Product.product_id == product_id).first()
            if new_primary:
                new_primary.is_primary = True
                if product:
                    product.primary_image_url = new_primary.image_url
                    product.primary_image_filename = new_primary.image_filename
            else:
                 if product:
                    product.primary_image_url = None
                    product.primary_image_filename = None
        
        db.commit()
        return {"detail": "Image deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting image: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete image")
