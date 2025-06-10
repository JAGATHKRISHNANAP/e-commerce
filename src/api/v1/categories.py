# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from typing import List
# from config.database import get_db
# from src.models.category import Category
# from src.schemas.category import CategoryResponse

# router = APIRouter()

# @router.get("/categories", response_model=List[CategoryResponse])
# async def get_categories(db: Session = Depends(get_db)):
#     """Get all categories"""
#     return db.query(Category).all()



# src/api/v1/categories.py - Clean Fixed Version

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
# from src.api.deps import get_db
from config.database import get_db
from src.schemas.category import CategoryResponse, CategoryCreate
from src.models.category import Category

router = APIRouter()

@router.get("", response_model=List[CategoryResponse])
async def get_categories(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all categories with optional filtering"""
    query = db.query(Category)
    
    if not include_inactive:
        query = query.filter(Category.is_active == True)
    
    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))
    
    categories = query.offset(skip).limit(limit).all()
    
    return [
        CategoryResponse(
            category_id=cat.category_id,
            name=cat.name,
            description=cat.description,
            is_active=cat.is_active,
            created_at=cat.created_at,
            updated_at=cat.updated_at
        ) for cat in categories
    ]

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get category by ID"""
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return CategoryResponse(
        category_id=category.category_id,
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at
    )

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(category_data: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category"""
    try:
        # Check if category name already exists
        existing = db.query(Category).filter(Category.name.ilike(category_data.name)).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Category with name '{category_data.name}' already exists"
            )
        
        # Create category
        category = Category(**category_data.dict(exclude_unset=True))
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return CategoryResponse(
            category_id=category.category_id,
            name=category.name,
            description=category.description,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create category: {str(e)}")

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, category_data: CategoryCreate, db: Session = Depends(get_db)):
    """Update a category"""
    try:
        category = db.query(Category).filter(Category.category_id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Check name uniqueness if changed
        if category_data.name and category_data.name.lower() != category.name.lower():
            existing = db.query(Category).filter(
                Category.name.ilike(category_data.name),
                Category.category_id != category_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Category with name '{category_data.name}' already exists"
                )
        
        # Update category fields
        update_data = category_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(category, key, value)
        
        db.commit()
        db.refresh(category)
        
        return CategoryResponse(
            category_id=category.category_id,
            name=category.name,
            description=category.description,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update category: {str(e)}")

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, force: bool = False, db: Session = Depends(get_db)):
    """Delete a category"""
    try:
        category = db.query(Category).filter(Category.category_id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Check if category has products
        from src.models.product import Product
        products_count = db.query(Product).filter(Product.category_id == category_id).count()
        
        if products_count > 0 and not force:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete category. It has {products_count} products associated with it. Use force=true to delete anyway."
            )
        
        # If force delete, set products category_id to NULL
        if products_count > 0 and force:
            db.query(Product).filter(Product.category_id == category_id).update({"category_id": None})
        
        db.delete(category)
        db.commit()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete category: {str(e)}")

@router.get("/{category_id}/products")
async def get_category_products(category_id: int, include_inactive: bool = False, db: Session = Depends(get_db)):
    """Get all products in a category"""
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    from src.models.product import Product
    query = db.query(Product).filter(Product.category_id == category_id)
    
    if not include_inactive:
        query = query.filter(Product.is_active == True)
    
    products = query.all()
    
    return {
        "category_id": category_id,
        "category_name": category.name,
        "category_description": category.description,
        "category_active": category.is_active,
        "products_count": len(products),
        "products": [
            {
                "product_id": p.product_id,
                "name": p.name,
                "description": p.description,
                "price": float(p.price),
                "stock_quantity": p.stock_quantity,
                "sku": p.sku,
                "brand": p.brand,
                "is_active": p.is_active,
                "created_at": p.created_at,
                "updated_at": p.updated_at
            } for p in products
        ]
    }

@router.patch("/{category_id}/toggle-status")
async def toggle_category_status(category_id: int, db: Session = Depends(get_db)):
    """Toggle category active/inactive status"""
    try:
        category = db.query(Category).filter(Category.category_id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        category.is_active = not category.is_active
        db.commit()
        db.refresh(category)
        
        return {
            "category_id": category_id,
            "name": category.name,
            "is_active": category.is_active,
            "message": f"Category {'activated' if category.is_active else 'deactivated'} successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to toggle category status: {str(e)}")