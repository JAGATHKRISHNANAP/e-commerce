# from pydantic import BaseModel

# class CategoryBase(BaseModel):
#     name: str

# class CategoryCreate(CategoryBase):
#     pass

# class CategoryResponse(CategoryBase):
#     category_id: int
    
#     class Config:
#         from_attributes = True


# src/schemas/category.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    category_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True