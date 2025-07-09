# src/api/v1/pricing.py - Fixed and complete
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from config.database import get_db
from src.models.category import PriceRule
from src.schemas.price_rule import PriceRuleResponse, PriceRuleCreate, PriceRuleUpdate
from src.schemas.product import PriceCalculationRequest, PriceCalculationResponse
from src.services.pricing_service import PricingService

router = APIRouter()

@router.post("/calculate-price", response_model=PriceCalculationResponse)
async def calculate_price(
    request: PriceCalculationRequest,
    db: Session = Depends(get_db)
):
    """Calculate price based on specifications"""
    try:
        pricing_service = PricingService(db)
        
        # Validate specifications first
        validation = pricing_service.validate_specifications(
            request.subcategory_id, 
            request.specifications
        )
        
        if not validation["is_valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid specifications: {'; '.join(validation['errors'])}"
            )
        
        # Calculate price
        final_price, applied_rules, price_breakdown = pricing_service.calculate_price(
            request.subcategory_id,
            request.specifications,
            request.base_price
        )
        
        return PriceCalculationResponse(
            base_price=price_breakdown.get("base_price", 0),
            calculated_price=final_price,
            applied_rules=applied_rules,
            price_breakdown=price_breakdown
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate price: {str(e)}")

@router.get("/subcategories/{subcategory_id}/price-rules", response_model=List[PriceRuleResponse])
async def get_price_rules(subcategory_id: int, db: Session = Depends(get_db)):
    """Get price rules for a subcategory"""
    rules = db.query(PriceRule).filter(
        PriceRule.subcategory_id == subcategory_id
    ).order_by(PriceRule.created_at.desc()).all()
    
    return rules

@router.post("/subcategories/{subcategory_id}/price-rules", response_model=PriceRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_price_rule(
    subcategory_id: int,
    rule_data: PriceRuleCreate,
    db: Session = Depends(get_db)
):
    """Create a new price rule"""
    try:
        pricing_service = PricingService(db)
        
        rule = pricing_service.create_price_rule(
            subcategory_id=subcategory_id,
            spec_conditions=rule_data.spec_conditions,
            base_price=rule_data.base_price,
            price_modifier=rule_data.price_modifier,
            modifier_type=rule_data.modifier_type.value,
            specification_template_id=rule_data.specification_template_id
        )
        
        return rule
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create price rule: {str(e)}")

@router.get("/price-rules/{rule_id}", response_model=PriceRuleResponse)
async def get_price_rule(rule_id: int, db: Session = Depends(get_db)):
    """Get price rule by ID"""
    rule = db.query(PriceRule).filter(PriceRule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Price rule not found")
    return rule

@router.put("/price-rules/{rule_id}", response_model=PriceRuleResponse)
async def update_price_rule(
    rule_id: int,
    rule_data: PriceRuleUpdate,
    db: Session = Depends(get_db)
):
    """Update a price rule"""
    rule = db.query(PriceRule).filter(PriceRule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Price rule not found")
    
    try:
        for field, value in rule_data.model_dump(exclude_unset=True).items():
            if field == "modifier_type" and value:
                setattr(rule, field, value.value)
            else:
                setattr(rule, field, value)
        
        db.commit()
        db.refresh(rule)
        return rule
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update price rule: {str(e)}")

@router.delete("/price-rules/{rule_id}")
async def delete_price_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a price rule"""
    rule = db.query(PriceRule).filter(PriceRule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Price rule not found")
    
    try:
        db.delete(rule)
        db.commit()
        return {"message": "Price rule deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete price rule: {str(e)}")

@router.get("/subcategories/{subcategory_id}/pricing-suggestions")
async def get_pricing_suggestions(subcategory_id: int, db: Session = Depends(get_db)):
    """Get pricing suggestions for missing spec combinations"""
    try:
        pricing_service = PricingService(db)
        suggestions = pricing_service.get_pricing_suggestions(subcategory_id)
        return {"suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pricing suggestions: {str(e)}")