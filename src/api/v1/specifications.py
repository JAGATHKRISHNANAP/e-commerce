# # src/api/v1/specifications.py - Specification template management
# from fastapi import APIRouter, Depends, HTTPException, status, Query
# from sqlalchemy.orm import Session
# from typing import List, Optional
# from config.database import get_db
# from src.models.category import SpecificationTemplate, Subcategory
# from src.schemas.specification_template import (
#     SpecificationTemplateResponse, 
#     SpecificationTemplateCreate, 
#     SpecificationTemplateUpdate
# )
# from src.schemas.subcategory import SubcategoryWithSpecsResponse

# router = APIRouter()

# @router.get("/subcategories/{subcategory_id}/specifications", response_model=List[SpecificationTemplateResponse])
# async def get_specification_templates(
#     subcategory_id: int,
#     is_active: Optional[bool] = Query(None),
#     db: Session = Depends(get_db)
# ):
#     """Get specification templates for a subcategory"""
#     # Verify subcategory exists
#     subcategory = db.query(Subcategory).filter(Subcategory.subcategory_id == subcategory_id).first()
#     if not subcategory:
#         raise HTTPException(status_code=404, detail="Subcategory not found")
    
#     query = db.query(SpecificationTemplate).filter(SpecificationTemplate.subcategory_id == subcategory_id)
#     if is_active is not None:
#         query = query.filter(SpecificationTemplate.is_active == is_active)
    
#     return query.order_by(SpecificationTemplate.display_order, SpecificationTemplate.spec_name).all()

# @router.post("/subcategories/{subcategory_id}/specifications", response_model=SpecificationTemplateResponse, status_code=status.HTTP_201_CREATED)
# async def create_specification_template(
#     subcategory_id: int,
#     spec_data: SpecificationTemplateCreate,
#     db: Session = Depends(get_db)
# ):
#     """Create a new specification template"""
#     # Verify subcategory exists
#     subcategory = db.query(Subcategory).filter(Subcategory.subcategory_id == subcategory_id).first()
#     if not subcategory:
#         raise HTTPException(status_code=404, detail="Subcategory not found")
    
#     try:
#         # Check if spec name already exists in this subcategory
#         existing = db.query(SpecificationTemplate).filter(
#             SpecificationTemplate.subcategory_id == subcategory_id,
#             SpecificationTemplate.spec_name == spec_data.spec_name
#         ).first()
        
#         if existing:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Specification '{spec_data.spec_name}' already exists in this subcategory"
#             )
        
#         spec_data.subcategory_id = subcategory_id
#         spec_template = SpecificationTemplate(**spec_data.dict())
#         db.add(spec_template)
#         db.commit()
#         db.refresh(spec_template)
#         return spec_template
        
#     except HTTPException:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to create specification template: {str(e)}")

# @router.get("/specifications/{template_id}", response_model=SpecificationTemplateResponse)
# async def get_specification_template(template_id: int, db: Session = Depends(get_db)):
#     """Get specification template by ID"""
#     template = db.query(SpecificationTemplate).filter(SpecificationTemplate.template_id == template_id).first()
#     if not template:
#         raise HTTPException(status_code=404, detail="Specification template not found")
#     return template

# @router.put("/specifications/{template_id}", response_model=SpecificationTemplateResponse)
# async def update_specification_template(
#     template_id: int,
#     spec_data: SpecificationTemplateUpdate,
#     db: Session = Depends(get_db)
# ):
#     """Update a specification template"""
#     template = db.query(SpecificationTemplate).filter(SpecificationTemplate.template_id == template_id).first()
#     if not template:
#         raise HTTPException(status_code=404, detail="Specification template not found")
    
#     try:
#         for field, value in spec_data.dict(exclude_unset=True).items():
#             setattr(template, field, value)
        
#         db.commit()
#         db.refresh(template)
#         return template
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to update specification template: {str(e)}")

# @router.delete("/specifications/{template_id}")
# async def delete_specification_template(template_id: int, db: Session = Depends(get_db)):
#     """Delete a specification template"""
#     template = db.query(SpecificationTemplate).filter(SpecificationTemplate.template_id == template_id).first()
#     if not template:
#         raise HTTPException(status_code=404, detail="Specification template not found")
    
#     try:
#         db.delete(template)
#         db.commit()
#         return {"message": "Specification template deleted successfully"}
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to delete specification template: {str(e)}")

# @router.get("/subcategories/{subcategory_id}/with-specifications", response_model=SubcategoryWithSpecsResponse)
# async def get_subcategory_with_specifications(subcategory_id: int, db: Session = Depends(get_db)):
#     """Get subcategory with its specification templates"""
#     subcategory = db.query(Subcategory).filter(Subcategory.subcategory_id == subcategory_id).first()
#     if not subcategory:
#         raise HTTPException(status_code=404, detail="Subcategory not found")
    
#     # Get specification templates
#     spec_templates = db.query(SpecificationTemplate).filter(
#         SpecificationTemplate.subcategory_id == subcategory_id,
#         SpecificationTemplate.is_active == True
#     ).order_by(SpecificationTemplate.display_order, SpecificationTemplate.spec_name).all()
    
#     return SubcategoryWithSpecsResponse(
#         **subcategory.__dict__,
#         spec_templates=spec_templates
#     )










# src/api/v1/specifications.py - Fixed version
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from config.database import get_db
from src.models.category import SpecificationTemplate, Subcategory
from src.schemas.specification_template import (
    SpecificationTemplateResponse, 
    SpecificationTemplateCreate, 
    SpecificationTemplateUpdate
)
from src.schemas.subcategory import SubcategoryWithSpecsResponse

router = APIRouter()

@router.get("/subcategories/{subcategory_id}/specifications", response_model=List[SpecificationTemplateResponse])
async def get_specification_templates(
    subcategory_id: int,
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get specification templates for a subcategory"""
    # Verify subcategory exists
    subcategory = db.query(Subcategory).filter(Subcategory.subcategory_id == subcategory_id).first()
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    
    query = db.query(SpecificationTemplate).filter(SpecificationTemplate.subcategory_id == subcategory_id)
    if is_active is not None:
        query = query.filter(SpecificationTemplate.is_active == is_active)
    
    return query.order_by(SpecificationTemplate.display_order, SpecificationTemplate.spec_name).all()

@router.post("/subcategories/{subcategory_id}/specifications", response_model=SpecificationTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_specification_template(
    subcategory_id: int,
    spec_data: SpecificationTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new specification template"""
    # Verify subcategory exists
    subcategory = db.query(Subcategory).filter(Subcategory.subcategory_id == subcategory_id).first()
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    
    try:
        # Check if spec name already exists in this subcategory
        existing = db.query(SpecificationTemplate).filter(
            SpecificationTemplate.subcategory_id == subcategory_id,
            SpecificationTemplate.spec_name == spec_data.spec_name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Specification '{spec_data.spec_name}' already exists in this subcategory"
            )
        
        # Create the specification template - subcategory_id comes from URL path
        spec_dict = spec_data.model_dump(exclude={'subcategory_id'})  # Remove subcategory_id from input
        spec_dict['subcategory_id'] = subcategory_id  # Use the one from URL path
        
        spec_template = SpecificationTemplate(**spec_dict)
        db.add(spec_template)
        db.commit()
        db.refresh(spec_template)
        return spec_template
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create specification template: {str(e)}")

@router.get("/specifications/{template_id}", response_model=SpecificationTemplateResponse)
async def get_specification_template(template_id: int, db: Session = Depends(get_db)):
    """Get specification template by ID"""
    template = db.query(SpecificationTemplate).filter(SpecificationTemplate.template_id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Specification template not found")
    return template

@router.put("/specifications/{template_id}", response_model=SpecificationTemplateResponse)
async def update_specification_template(
    template_id: int,
    spec_data: SpecificationTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a specification template"""
    template = db.query(SpecificationTemplate).filter(SpecificationTemplate.template_id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Specification template not found")
    
    try:
        for field, value in spec_data.model_dump(exclude_unset=True).items():
            setattr(template, field, value)
        
        db.commit()
        db.refresh(template)
        return template
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update specification template: {str(e)}")

@router.delete("/specifications/{template_id}")
async def delete_specification_template(template_id: int, db: Session = Depends(get_db)):
    """Delete a specification template"""
    template = db.query(SpecificationTemplate).filter(SpecificationTemplate.template_id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Specification template not found")
    
    try:
        db.delete(template)
        db.commit()
        return {"message": "Specification template deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete specification template: {str(e)}")

@router.get("/subcategories/{subcategory_id}/with-specifications", response_model=SubcategoryWithSpecsResponse)
async def get_subcategory_with_specifications(subcategory_id: int, db: Session = Depends(get_db)):
    """Get subcategory with its specification templates"""
    subcategory = db.query(Subcategory).filter(Subcategory.subcategory_id == subcategory_id).first()
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    
    # Get specification templates
    spec_templates = db.query(SpecificationTemplate).filter(
        SpecificationTemplate.subcategory_id == subcategory_id,
        SpecificationTemplate.is_active == True
    ).order_by(SpecificationTemplate.display_order, SpecificationTemplate.spec_name).all()
    
    return SubcategoryWithSpecsResponse(
        **subcategory.__dict__,
        spec_templates=spec_templates
    )