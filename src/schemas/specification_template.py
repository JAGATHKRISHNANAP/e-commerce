# src/schemas/specification_template.py - Fixed schema
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class SpecTypeEnum(str, Enum):
    SELECT = "select"
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"

class SpecificationTemplateBase(BaseModel):
    spec_name: str = Field(..., min_length=1, max_length=100)
    spec_type: SpecTypeEnum
    spec_options: Optional[List[str]] = None  # For select type
    is_required: bool = False
    affects_price: bool = False
    display_order: int = 0
    is_active: bool = True

class SpecificationTemplateCreate(SpecificationTemplateBase):
    # Don't include subcategory_id here - it comes from the URL path
    pass

class SpecificationTemplateUpdate(BaseModel):
    spec_name: Optional[str] = Field(None, min_length=1, max_length=100)
    spec_type: Optional[SpecTypeEnum] = None
    spec_options: Optional[List[str]] = None
    is_required: Optional[bool] = None
    affects_price: Optional[bool] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

class SpecificationTemplateResponse(SpecificationTemplateBase):
    template_id: int
    subcategory_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True