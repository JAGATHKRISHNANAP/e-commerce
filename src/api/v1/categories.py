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




# # src/api/v1/categories.py - With POST endpoint added

# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List
# from config.database import get_db
# from src.models.category import Category
# from src.schemas.category import CategoryResponse, CategoryCreate

# router = APIRouter()

# @router.get("/categories", response_model=List[CategoryResponse])
# async def get_categories(db: Session = Depends(get_db)):
#     """Get all categories"""
#     return db.query(Category).all()

# @router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
# async def create_category(category_data: CategoryCreate, db: Session = Depends(get_db)):
#     """Create a new category"""
#     try:
#         # Check if category name already exists
#         existing = db.query(Category).filter(Category.name == category_data.name).first()
#         if existing:
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Category with name '{category_data.name}' already exists"
#             )
        
#         # Create new category
#         category = Category(name=category_data.name)
#         db.add(category)
#         db.commit()
#         db.refresh(category)
        
#         return category
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to create category: {str(e)}")

# @router.get("/categories/{category_id}", response_model=CategoryResponse)
# async def get_category(category_id: int, db: Session = Depends(get_db)):
#     """Get category by ID"""
#     category = db.query(Category).filter(Category.category_id == category_id).first()
#     if not category:
#         raise HTTPException(status_code=404, detail="Category not found")
#     return category













# src/api/v1/categories.py - Simplified version that works with your existing setup
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from config.database import get_db

# Try to import the new models, fall back to existing ones if they don't exist
try:
    from src.models.category import Category, Subcategory
except ImportError:
    from src.models.category import Category
    # Define a simple Subcategory model if it doesn't exist
    from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    from config.database import Base
    
    class Subcategory(Base):
        __tablename__ = "subcategories"
        
        subcategory_id = Column(Integer, primary_key=True, index=True)
        category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
        name = Column(String(100), nullable=False, index=True)
        description = Column(Text, nullable=True)
        is_active = Column(Boolean, default=True, nullable=False)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
        updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
        
        category = relationship("Category")

# Try to import new schemas, fall back to existing ones
try:
    from src.schemas.category import CategoryResponse, CategoryCreate
    from src.schemas.subcategory import SubcategoryResponse, SubcategoryCreate
except ImportError:
    # Use your existing category schema
    from pydantic import BaseModel
    from typing import Optional
    from datetime import datetime
    
    class CategoryCreate(BaseModel):
        name: str
        description: Optional[str] = None
    
    class CategoryResponse(BaseModel):
        category_id: int
        name: str
        description: Optional[str] = None
        
        class Config:
            from_attributes = True
    
    class SubcategoryCreate(BaseModel):
        name: str
        description: Optional[str] = None
        category_id: int
    
    class SubcategoryResponse(BaseModel):
        subcategory_id: int
        category_id: int
        name: str
        description: Optional[str] = None
        
        class Config:
            from_attributes = True

router = APIRouter()

# Your existing categories endpoint
@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    return db.query(Category).all()

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(category_data: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category"""
    try:
        existing = db.query(Category).filter(Category.name == category_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Category '{category_data.name}' already exists")
        
        category = Category(
            name=category_data.name,
            description=category_data.description
        )
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

# New subcategory endpoints
@router.get("/categories/{category_id}/subcategories", response_model=List[SubcategoryResponse])
async def get_subcategories(category_id: int, db: Session = Depends(get_db)):
    """Get subcategories for a category"""
    # Verify category exists
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    subcategories = db.query(Subcategory).filter(Subcategory.category_id == category_id).all()
    return subcategories

@router.post("/categories/{category_id}/subcategories", response_model=SubcategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_subcategory(
    category_id: int,
    subcategory_data: SubcategoryCreate,
    db: Session = Depends(get_db)
):
    """Create a new subcategory"""
    # Verify category exists
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    try:
        # Check if subcategory name already exists in this category
        existing = db.query(Subcategory).filter(
            Subcategory.category_id == category_id,
            Subcategory.name == subcategory_data.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Subcategory '{subcategory_data.name}' already exists in this category"
            )
        
        subcategory = Subcategory(
            category_id=category_id,
            name=subcategory_data.name,
            description=subcategory_data.description
        )
        db.add(subcategory)
        db.commit()
        db.refresh(subcategory)
        return subcategory
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create subcategory: {str(e)}")

@router.get("/subcategories/{subcategory_id}", response_model=SubcategoryResponse)
async def get_subcategory(subcategory_id: int, db: Session = Depends(get_db)):
    """Get subcategory by ID"""
    subcategory = db.query(Subcategory).filter(Subcategory.subcategory_id == subcategory_id).first()
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return subcategory