# src/schemas/category.py
from pydantic import BaseModel

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    category_id: int
    
    class Config:
        from_attributes = True

