# src/schemas/subcategory.py - Fixed
from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from .specification_template import SpecificationTemplateResponse

# # Import only for type checking to avoid circular imports
# if TYPE_CHECKING:
#     from .specification_template import SpecificationTemplateResponse

class SubcategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True

class SubcategoryCreate(SubcategoryBase):
    category_id: int

class SubcategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class SubcategoryResponse(SubcategoryBase):
    subcategory_id: int
    category_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SubcategoryWithSpecsResponse(SubcategoryResponse):
    spec_templates: List['SpecificationTemplateResponse'] = []