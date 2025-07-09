# src/schemas/price_rule.py - Fixed for Pydantic v2
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class ModifierTypeEnum(str, Enum):
    ADD = "add"
    MULTIPLY = "multiply"
    SET = "set"

class PriceRuleBase(BaseModel):
    base_price: int = Field(..., gt=0)  # Price in cents
    spec_conditions: Dict[str, Any] = Field(..., min_length=1)
    price_modifier: int = 0
    modifier_type: ModifierTypeEnum = ModifierTypeEnum.ADD
    is_active: bool = True

class PriceRuleCreate(PriceRuleBase):
    # Remove subcategory_id - it comes from URL path
    specification_template_id: Optional[int] = None

class PriceRuleUpdate(BaseModel):
    base_price: Optional[int] = Field(None, gt=0)
    spec_conditions: Optional[Dict[str, Any]] = None
    price_modifier: Optional[int] = None
    modifier_type: Optional[ModifierTypeEnum] = None
    is_active: Optional[bool] = None

class PriceRuleResponse(PriceRuleBase):
    rule_id: int
    subcategory_id: int
    specification_template_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True