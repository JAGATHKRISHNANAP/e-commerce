# # src/schemas/category.py
# from pydantic import BaseModel

# class CategoryBase(BaseModel):
#     name: str

# class CategoryCreate(CategoryBase):
#     pass

# class CategoryResponse(CategoryBase):
#     category_id: int
    
#     class Config:
#         from_attributes = True




# src/schemas/category.py - Fixed
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase):
    category_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True