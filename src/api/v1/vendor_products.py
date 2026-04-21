# src/api/v1/vendor_products.py
# Vendor-scoped reads. Writes still go through /api/v1/products* — those
# endpoints are hardened to derive ownership from the vendor JWT.
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, func
from typing import Optional
import logging

from config.database import get_db
from src.models.product import Product
from src.models.product_image import ProductImage
from src.models.vendor import Vendor
from src.schemas.product import ProductResponse, ProductListResponse
from src.api.v1.vender_auth import get_current_user as get_current_vendor

logger = logging.getLogger(__name__)

router = APIRouter()


def _vendor_discounted_price(product: Product) -> int:
    base = product.calculated_price if product.calculated_price is not None else product.base_price
    if base is None:
        return 0
    pct = product.discount_percent or 0
    if pct <= 0:
        return int(base)
    return int(round(base * (100 - pct) / 100))


@router.get("/products", response_model=ProductListResponse)
async def list_vendor_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=1000),
    category_id: Optional[int] = Query(None),
    subcategory_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    group_products: bool = Query(False),
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    """List products owned by the current vendor (filtered by `created_by == vendor_ph_no`)."""
    vendor_identifier = current_vendor.vendor_ph_no

    query = db.query(Product).options(
        joinedload(Product.category),
        joinedload(Product.subcategory),
        joinedload(Product.images),
    ).filter(Product.created_by == vendor_identifier)

    if group_products:
        subquery = (
            db.query(func.min(Product.product_id).label("min_id"))
            .filter(Product.created_by == vendor_identifier)
            .group_by(Product.group_id)
            .subquery()
        )
        query = query.join(subquery, Product.product_id == subquery.c.min_id)

    if category_id is not None and category_id > 0:
        query = query.filter(Product.category_id == category_id)
    if subcategory_id is not None and subcategory_id > 0:
        query = query.filter(Product.subcategory_id == subcategory_id)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    if min_price is not None:
        query = query.filter(
            func.coalesce(Product.calculated_price, Product.base_price) >= int(min_price * 100)
        )
    if max_price is not None:
        query = query.filter(
            func.coalesce(Product.calculated_price, Product.base_price) <= int(max_price * 100)
        )

    if sort_by == "price":
        price_col = func.coalesce(Product.calculated_price, Product.base_price)
        query = query.order_by(desc(price_col) if sort_order.lower() == "desc" else asc(price_col))
    elif sort_by == "created_at":
        query = query.order_by(desc(Product.created_at) if sort_order.lower() == "desc" else asc(Product.created_at))
    else:
        query = query.order_by(desc(Product.name) if sort_order.lower() == "desc" else asc(Product.name))

    total_count = query.count()
    offset = (page - 1) * per_page
    products = query.offset(offset).limit(per_page).all()

    product_responses = []
    for product in products:
        product_responses.append(ProductResponse(
            product_id=product.product_id,
            name=product.name,
            description=product.description,
            category_id=product.category_id,
            subcategory_id=product.subcategory_id,
            specifications=product.specifications,
            base_price=product.base_price,
            calculated_price=product.calculated_price,
            discount_percent=product.discount_percent or 0,
            discounted_price=_vendor_discounted_price(product),
            stock_quantity=product.stock_quantity,
            sku=product.sku,
            is_active=product.is_active,
            created_by=product.created_by,
            created_at=product.created_at,
            updated_at=product.updated_at,
            category={
                "category_id": product.category.category_id,
                "name": product.category.name,
                "description": product.category.description,
            } if product.category else None,
            subcategory={
                "subcategory_id": product.subcategory.subcategory_id,
                "name": product.subcategory.name,
                "description": product.subcategory.description,
            } if product.subcategory else None,
            primary_image_url=product.primary_image_url,
            primary_image_filename=product.primary_image_filename,
        ))

    total_pages = (total_count + per_page - 1) // per_page
    return ProductListResponse(
        products=product_responses,
        total_count=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_vendor_product(
    product_id: int,
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    """Get one of the current vendor's own products. 404 if owned by someone else."""
    product = db.query(Product).options(
        joinedload(Product.category),
        joinedload(Product.subcategory),
        joinedload(Product.images),
    ).filter(
        Product.product_id == product_id,
        Product.created_by == current_vendor.vendor_ph_no,
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductResponse(
        product_id=product.product_id,
        name=product.name,
        description=product.description,
        category_id=product.category_id,
        subcategory_id=product.subcategory_id,
        specifications=product.specifications,
        base_price=product.base_price,
        calculated_price=product.calculated_price,
        discount_percent=product.discount_percent or 0,
        discounted_price=_vendor_discounted_price(product),
        stock_quantity=product.stock_quantity,
        sku=product.sku,
        is_active=product.is_active,
        created_by=product.created_by,
        created_at=product.created_at,
        updated_at=product.updated_at,
        category={
            "category_id": product.category.category_id,
            "name": product.category.name,
            "description": product.category.description,
        } if product.category else None,
        subcategory={
            "subcategory_id": product.subcategory.subcategory_id,
            "name": product.subcategory.name,
            "description": product.subcategory.description,
        } if product.subcategory else None,
        primary_image_url=product.primary_image_url,
        primary_image_filename=product.primary_image_filename,
    )


@router.get("/products/{product_id}/images")
async def get_vendor_product_images(
    product_id: int,
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    """Get images for a product owned by the current vendor."""
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.created_by == current_vendor.vendor_ph_no,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    images = db.query(ProductImage).filter(
        ProductImage.product_id == product_id
    ).order_by(ProductImage.display_order).all()

    return {
        "product_id": product_id,
        "images": [
            {
                "image_id": img.image_id,
                "image_url": img.image_url,
                "filename": img.image_filename,
                "is_primary": img.is_primary,
                "display_order": img.display_order,
            } for img in images
        ],
    }
