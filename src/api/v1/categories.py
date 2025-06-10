# # src/api/v1/categories.py
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




# src/api/v1/categories.py - With POST endpoint added

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from config.database import get_db
from src.models.category import Category
from src.schemas.category import CategoryResponse, CategoryCreate

router = APIRouter()

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    return db.query(Category).all()

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(category_data: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category"""
    try:
        # Check if category name already exists
        existing = db.query(Category).filter(Category.name == category_data.name).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Category with name '{category_data.name}' already exists"
            )
        
        # Create new category
        category = Category(name=category_data.name)
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return category
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create category: {str(e)}")

@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get category by ID"""
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category